import csv
import argparse
from db.models import get_session, EnrichedProspect


def export_db(db_url: str, output_path: str):
    session = get_session(db_url)
    qs = session.query(EnrichedProspect).all()
    fieldnames = ['id', 'source_row_id', 'primary_email_domain', 'dns_mx', 'dns_txt', 'dns_ns', 'dns_score', 'phones_summary']
    with open(output_path, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for p in qs:
            writer.writerow({
                'id': p.id,
                'source_row_id': p.source_row_id,
                'primary_email_domain': p.primary_email_domain,
                'dns_mx': p.dns_mx,
                'dns_txt': p.dns_txt,
                'dns_ns': p.dns_ns,
                'dns_score': p.dns_score,
                'phones_summary': p.phones_summary,
            })
    session.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db-url', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    export_db(args.db_url, args.output)


if __name__ == '__main__':
    main()
