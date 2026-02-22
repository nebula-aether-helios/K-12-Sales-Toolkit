"""Command-line runner for seeding and ingesting datasets."""
import argparse
from . import storage
from .ingest import ingest_sources_from_csv


def main():
    parser = argparse.ArgumentParser(description='Catalog API runner')
    parser.add_argument('--init-db', action='store_true', help='Initialize the SQLite DB')
    parser.add_argument('--seed-csv', type=str, help='Path to CSV to seed datasets')
    parser.add_argument('--site-base', type=str, help='Site base URL for Socrata/CKAN')
    args = parser.parse_args()

    if args.init_db:
        storage.init_db()
        print('Initialized DB')

    if args.seed_csv:
        if not args.site_base:
            print('Using default site base from config')
        ingest_sources_from_csv(args.seed_csv, site_base=args.site_base)


if __name__ == '__main__':
    main()
