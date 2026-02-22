"""Seed the enrichment DB with test contractors for local runs.

Usage: python scripts/seed_contractors.py --db outputs/enrichment.db --count 1000
"""
import argparse
from src.enrichment_models import EnrichmentDB


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default='outputs/enrichment.db')
    parser.add_argument('--count', type=int, default=1000)
    args = parser.parse_args()

    db = EnrichmentDB(args.db)
    db.create_all()

    for i in range(1, args.count + 1):
        lic = f"TEST{i:05d}"
        name = f"TestCo {i}"
        db.upsert_contractor(license_number=lic, business_name=name)

    print(f"Seeded {args.count} contractors into {args.db}")


if __name__ == '__main__':
    main()
