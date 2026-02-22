import time
from typing import List

from db.models import get_session, EnrichedProspect, EmailCandidate
from enrichment.email_utils import apply_acceptance_rules, smtp_probe, detect_catch_all


def prospects_for_iteration(session, limit=10):
    # pick the first `limit` prospects by source_row_id (string of 1..N)
    ps = session.query(EnrichedProspect).filter(EnrichedProspect.source_row_id != None).order_by(EnrichedProspect.id).limit(limit).all()
    return ps


def reprobe_prospect(session, p: EnrichedProspect):
    updated = False
    mx = p.dns_mx or []
    spf = []
    try:
        spf = p.dns_txt or []
    except Exception:
        spf = []
    for c in list(p.emails):
        if c.status == 'validated_smtp':
            continue
        # only probe candidates where MX present
        if not mx:
            continue
        try:
            is_catch = detect_catch_all(mx, p.primary_email_domain or '')
        except Exception:
            is_catch = False
        if is_catch:
            c.status = 'catch_all'
            session.add(c)
            updated = True
            continue
        try:
            probe = smtp_probe(c.email, mx)
        except Exception as e:
            probe = {'status': 'unknown', 'details': str(e)}
        st = probe.get('status')
        if st == 'valid':
            c.status = 'validated_smtp'
        elif st == 'invalid':
            c.status = 'invalid_smtp'
        else:
            c.status = 'unknown_smtp'
        c.source_signals = c.source_signals or {}
        c.source_signals['smtp_details'] = probe.get('details')
        session.add(c)
        updated = True
    if updated:
        session.commit()


def apply_rules_and_purge(session, p: EnrichedProspect):
    # build prospect signals
    signals = {'dns_mx': p.dns_mx, 'dns_txt': p.dns_txt, 'catch_all': False}
    # call acceptance rules
    candidates = []
    for c in p.emails:
        candidates.append({'email': c.email, 'score': float(c.score or 0.0), 'status': c.status})
    new = apply_acceptance_rules(candidates, prospect_signals=signals)
    # update DB rows and purge those marked purged
    for item in new:
        row = session.query(EmailCandidate).filter(EmailCandidate.email == item['email'], EmailCandidate.prospect_id == p.id).first()
        if not row:
            continue
        row.status = item.get('final_status') or row.status
        session.add(row)
        if row.status == 'purged':
            session.delete(row)
    session.commit()


def success_metric(session, prospects: List[EnrichedProspect]):
    total = len(prospects)
    if total == 0:
        return 0.0
    good = 0
    for p in prospects:
        has_valid = any((e.status == 'validated_smtp' or (e.status and e.status in ('high_confidence', 'validated'))) for e in p.emails)
        if has_valid:
            good += 1
    return good / total


def run(db_url: str, limit: int = 10, max_iters: int = 10, sleep_between: float = 1.0):
    session = get_session(db_url)
    prospects = prospects_for_iteration(session, limit=limit)
    it = 0
    while it < max_iters:
        it += 1
        print(f"Iteration {it}: reprobing {len(prospects)} prospects")
        for p in prospects:
            # refresh instance
            session.refresh(p)
            reprobe_prospect(session, p)
            # refresh emails relationship
            session.refresh(p)
            apply_rules_and_purge(session, p)
        # recompute prospects list and metric
        prospects = prospects_for_iteration(session, limit=limit)
        metric = success_metric(session, prospects)
        print(f"  success_metric={metric:.3f}")
        if metric >= 0.99:
            print("Reached 99% success metric, stopping.")
            break
        time.sleep(sleep_between)
    session.close()


if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('--db-url', required=True)
    p.add_argument('--limit', type=int, default=10)
    p.add_argument('--max-iters', type=int, default=10)
    p.add_argument('--sleep', type=float, default=1.0)
    args = p.parse_args()
    run(args.db_url, limit=args.limit, max_iters=args.max_iters, sleep_between=args.sleep)
