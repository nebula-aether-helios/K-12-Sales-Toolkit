import csv
import argparse
from typing import List
from db.models import get_session, EnrichedProspect


def export_email_candidates(db_url: str, output_path: str):
    session = get_session(db_url)
    rows: List[dict] = []
    for p in session.query(EnrichedProspect).all():
        # if there are email candidates, export one row per candidate
        if p.emails:
            for e in p.emails:
                rows.append({
                    'prospect_id': p.id,
                    'source_row_id': p.source_row_id,
                    'primary_email_domain': p.primary_email_domain,
                    'dns_mx': p.dns_mx,
                    'dns_txt': p.dns_txt,
                    'dns_ns': p.dns_ns,
                    'dns_score': p.dns_score,
                    'email': e.email,
                    'email_status': e.status,
                    'email_score': e.score,
                })
        else:
            rows.append({
                'prospect_id': p.id,
                'source_row_id': p.source_row_id,
                'primary_email_domain': p.primary_email_domain,
                'dns_mx': p.dns_mx,
                'dns_txt': p.dns_txt,
                'dns_ns': p.dns_ns,
                'dns_score': p.dns_score,
                'email': None,
                'email_status': None,
                'email_score': None,
            })

    fieldnames = ['prospect_id', 'source_row_id', 'primary_email_domain', 'dns_mx', 'dns_txt', 'dns_ns', 'dns_score', 'email', 'email_status', 'email_score']
    with open(output_path, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    session.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db-url', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    export_email_candidates(args.db_url, args.output)


if __name__ == '__main__':
    main()
