import datetime
import os
from db.models import get_session, EnrichedProspect, EmailCandidate


def generate(db_url: str, out_dir: str = 'snapshots') -> str:
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    path = os.path.join(out_dir, f'critical_state_{ts}.txt')
    session = get_session(db_url)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(f'Critical state snapshot generated: {ts}\n')
        fh.write(f'DB URL: {db_url}\n\n')
        p_count = session.query(EnrichedProspect).count()
        e_count = session.query(EmailCandidate).count()
        fh.write(f'Prospect count: {p_count}\n')
        fh.write(f'Email candidate count: {e_count}\n\n')
        fh.write('Sample prospects (first 10):\n')
        for p in session.query(EnrichedProspect).order_by(EnrichedProspect.id).limit(10).all():
            fh.write(f'ID={p.id} src_row={p.source_row_id} domain={p.primary_email_domain} dns_mx={bool(p.dns_mx)} emails={len(p.emails)}\n')
        fh.write('\nSample email candidates (first 20):\n')
        for e in session.query(EmailCandidate).order_by(EmailCandidate.id).limit(20).all():
            fh.write(f'ID={e.id} prospect_id={e.prospect_id} email={e.email} status={e.status} score={e.score}\n')
        fh.write('\nRecent files:\n')
        files = [
            'outputs/sample_10_email_candidates.csv',
            'outputs/sacramento_contractors_cslb_sac_osint.csv',
            'enrichment/email_utils.py',
            'workers/quick_run.py',
            'tools/iterative_validate.py',
            'tools/purge_non_validated.py'
        ]
        for f in files:
            try:
                stat = os.stat(f)
                fh.write(f"{f} - size={stat.st_size} modified={datetime.datetime.utcfromtimestamp(stat.st_mtime).isoformat()}Z\n")
            except Exception:
                fh.write(f"{f} - MISSING\n")
    session.close()
    return path


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--db-url', required=True)
    p.add_argument('--out-dir', default='snapshots')
    args = p.parse_args()
    path = generate(args.db_url, args.out_dir)
    print(f'Wrote snapshot to: {path}')
