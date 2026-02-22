import json
import argparse
import pika
import time
from db.models import get_session, EnrichedProspect, EmailCandidate, Phone
from connectors.dns_helpers import get_dns_records, parse_spf, mx_provider_from_hostname
from enrichment.email_utils import generate_email_candidates, choose_best_candidates, smtp_probe, detect_catch_all
from enrichment.phone_utils import parse_phone_number


def process_task(body: bytes, db_url: str, enable_smtp: bool = False):
    task = json.loads(body)
    row = task.get('row', {})
    row_index = task.get('row_index')
    name_cols = task.get('name_cols', [])
    phone_cols = task.get('phone_cols', [])
    owner_cols = task.get('owner_cols', [])
    # derive domain: try business website or email domain columns
    domain = None
    for k in ('website', 'domain', 'email_domain', 'business_domain'):
        if k in row and row[k]:
            domain = row[k]
            break
    if not domain:
        # fallback: try to derive from business name
        domain = (row.get('business_name') or row.get('company') or '').strip()
        if domain and ' ' in domain:
            domain = domain.split(' ')[0] + '.com'
    dns = get_dns_records(domain) if domain else {}
    # normalize domain before DNS lookups
    from connectors.dns_helpers import normalize_domain
    domain = normalize_domain(domain) if domain else domain
    dns = get_dns_records(domain) if domain else {}
    spf = parse_spf(dns.get('txt', [])) if dns else {'has_spf': False, 'includes': []}
    primary_email_domain = None
    if dns.get('mx'):
        primary_email_domain = dns['mx'][0][1]
    # build DB row
    session = get_session(db_url)
    prospect = EnrichedProspect(
        source_row_id=str(row_index),
        primary_email_domain=primary_email_domain,
        dns_mx=dns.get('mx'),
        dns_txt=dns.get('txt'),
        dns_ns=dns.get('ns'),
        dns_score=1 if dns.get('mx') else 0,
        phones_summary={},
    )
    session.add(prospect)
    session.commit()
    # process personnel names
    for name_col in name_cols:
        name_val = row.get(name_col)
        if not name_val:
            continue
        # naive split
        parts = name_val.split()
        first = parts[0]
        last = parts[-1] if len(parts) > 1 else ''
        domain_to_use = primary_email_domain or domain
        # enumerate usernames to enhance hypotheses
        try:
            from enrichment.email_utils import enumerate_usernames, hypothesize_from_usernames
            usernames = enumerate_usernames(first, last)
            username_hypotheses = hypothesize_from_usernames(usernames, domain_to_use)
        except Exception:
            usernames = []
            username_hypotheses = []
        candidates = generate_email_candidates(first, last, domain_to_use)
        for uh in username_hypotheses:
            if uh not in candidates:
                candidates.append(uh)
        best = choose_best_candidates(candidates, {'provider': mx_provider_from_hostname(primary_email_domain or '')}, spf.get('includes', []), username_hits=usernames, top_n=7)
        is_owner = owner_cols and name_col in owner_cols
        for c in best:
            details = None
            if not dns.get('mx'):
                status = 'no_mx'
            else:
                status = 'mx_present_unverified'
            if enable_smtp and dns.get('mx'):
                try:
                    is_catch = detect_catch_all(dns.get('mx', []), primary_email_domain or domain)
                except Exception:
                    is_catch = False
                if is_catch:
                    status = 'catch_all'
                    details = 'catch_all_detected'
                else:
                    try:
                        probe = smtp_probe(c['email'], dns.get('mx', []))
                        if probe.get('status') == 'valid':
                            status = 'validated_smtp'
                            details = probe.get('details')
                        elif probe.get('status') == 'invalid':
                            status = 'invalid_smtp'
                            details = probe.get('details')
                        else:
                            status = 'unknown_smtp'
                            details = probe.get('details')
                    except Exception:
                        status = 'unknown_smtp'
            ec = EmailCandidate(
                prospect_id=prospect.id,
                email=c['email'],
                pattern='generated',
                score=str(c['score']),
                status=status,
                source_signals={'spf': spf, 'mx': dns.get('mx'), 'smtp_details': details, 'username_hits': usernames, 'is_owner': bool(is_owner)},
            )
            session.add(ec)
    # process phones
    phones_summary = {}
    for pcol in phone_cols:
        raw = row.get(pcol)
        if not raw:
            continue
        pinfo = parse_phone_number(raw)
        phone = Phone(
            prospect_id=prospect.id,
            raw=raw,
            normalized=pinfo.get('normalized'),
            valid=str(pinfo.get('valid')),
            type=pinfo.get('type'),
            carrier_guess=pinfo.get('carrier'),
        )
        session.add(phone)
        phones_summary[pcol] = pinfo
    prospect.phones_summary = phones_summary
    session.commit()
    session.close()


def consume(rabbitmq_url: str, queue: str, db_url: str):
    conn = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
    ch = conn.channel()
    ch.queue_declare(queue=queue, durable=True)

    def callback(ch, method, properties, body):
        try:
            process_task(body, db_url, enable_smtp=enable_smtp)
        except Exception as e:
            print("task error:", e)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(queue=queue, on_message_callback=callback)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    try:
        ch.start_consuming()
    except KeyboardInterrupt:
        ch.stop_consuming()
    conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rabbitmq-url', required=True)
    parser.add_argument('--queue', default='enrich_tasks')
    parser.add_argument('--db-url', default='sqlite:///enrichment.db')
    parser.add_argument('--enable-smtp', action='store_true', help='Enable SMTP RCPT probes (may require port 25)')
    args = parser.parse_args()
    global enable_smtp
    enable_smtp = args.enable_smtp
    consume(args.rabbitmq_url, args.queue, args.db_url)


if __name__ == '__main__':
    main()
