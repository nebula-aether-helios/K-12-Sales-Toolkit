import csv
import sys

def main(path: str, limit: int = 10):
    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for idx, row in enumerate(reader, start=1):
            if idx > limit:
                break
            vals = {k: row.get(k) for k in ('website','domain','email_domain','business_domain','derived_domain','osint_email_domain','gp_website')}
            print(f'row={idx} derived: {vals}')


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('path')
    p.add_argument('--limit', type=int, default=10)
    args = p.parse_args()
    main(args.path, args.limit)
