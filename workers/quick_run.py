import csv
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from connectors.dns_helpers import get_dns_records, parse_spf, mx_provider_from_hostname
from enrichment.email_utils import generate_email_candidates, choose_best_candidates, smtp_probe, detect_catch_all
from enrichment.phone_utils import parse_phone_number
from db.models import create_tables, get_session, EnrichedProspect, EmailCandidate, Phone


def autodetect_personnel_columns(header: List[str]):
    name_cols = [h for h in header if any(x in h.lower() for x in ("name", "first", "last", "person"))]
    phone_cols = [h for h in header if any(x in h.lower() for x in ("phone", "mobile", "cell", "work"))]
    owner_cols = [h for h in header if any(x in h.lower() for x in ("owner", "registered", "principal", "owner_name"))]
    return name_cols, phone_cols, owner_cols


def derive_domain_from_row(row: dict) -> str:
    # check several common fields that may contain a usable domain from enrichment
    for k in ('website', 'domain', 'email_domain', 'business_domain', 'derived_domain', 'osint_email_domain', 'gp_website'):
        if k in row and row[k]:
            from connectors.dns_helpers import normalize_domain
            return normalize_domain(row[k])
    # fallback: try to derive from business name
    domain = (row.get('business_name') or row.get('company') or '').strip()
    if not domain:
        return ''
    # if business name contains spaces, take first token as base and normalize
    base = domain.split(' ')[0]
    from connectors.dns_helpers import normalize_domain
    return normalize_domain(base)


def process_row(row_index: int, row: dict, name_cols: List[str], phone_cols: List[str], db_url: str, enable_smtp: bool = False, owner_cols: List[str] = None):
    domain = derive_domain_from_row(row)
    dns = get_dns_records(domain) if domain else {}
    spf = parse_spf(dns.get('txt', [])) if dns else {'has_spf': False, 'includes': []}
    primary_email_domain = None
    if dns.get('mx'):
        primary_email_domain = dns['mx'][0][1]

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

    # personnel
    for name_col in name_cols:
        name_val = row.get(name_col)
        if not name_val:
            continue
        parts = name_val.split()
        first = parts[0]
        last = parts[-1] if len(parts) > 1 else ''
        domain_to_use = primary_email_domain or domain
        # enumerate possible usernames from public sources (GitHub) to improve hypotheses
        try:
            from enrichment.email_utils import enumerate_usernames, hypothesize_from_usernames
            usernames = enumerate_usernames(first, last)
            username_hypotheses = hypothesize_from_usernames(usernames, domain_to_use)
        except Exception:
            usernames = []
            username_hypotheses = []
        candidates = generate_email_candidates(first, last, domain_to_use)
        # extend with username-derived hypotheses (dedupe)
        for uh in username_hypotheses:
            if uh not in candidates:
                candidates.append(uh)
        # Keep up to 7 hypotheses per person
        best = choose_best_candidates(candidates, {'provider': mx_provider_from_hostname(primary_email_domain or '')}, spf.get('includes', []), username_hits=usernames, top_n=7)
        is_owner = owner_cols and name_col in owner_cols
        for c in best:
            details = None
            # MX presence check
            if not dns.get('mx'):
                status = 'no_mx'
            else:
                status = 'mx_present_unverified'
            # Optional SMTP probing
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

    # phones
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
    return prospect.id


def run_quick(input_csv: str, db_url: str, limit: int = 500, workers: int = 4, enable_smtp: bool = False):
    create_tables(db_url)
    tasks = []
    with open(input_csv, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames
        name_cols, phone_cols, owner_cols = autodetect_personnel_columns(header)
        for idx, row in enumerate(reader, start=1):
            if idx > limit:
                break
            tasks.append((idx, row, name_cols, phone_cols, owner_cols))

    results = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(process_row, idx, row, name_cols, phone_cols, db_url, enable_smtp, owner_cols) for (idx, row, name_cols, phone_cols, owner_cols) in tasks]
        for fut in as_completed(futures):
            try:
                results.append(fut.result())
            except Exception as e:
                print('task error', e)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--db-url', default='sqlite:///enrichment.db')
    parser.add_argument('--limit', type=int, default=500)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--enable-smtp', action='store_true', help='Enable SMTP RCPT probes (may require port 25)')
    args = parser.parse_args()
    ids = run_quick(args.input, args.db_url, args.limit, args.workers, args.enable_smtp)
    print(f'Processed {len(ids)} rows')


if __name__ == '__main__':
    main()
