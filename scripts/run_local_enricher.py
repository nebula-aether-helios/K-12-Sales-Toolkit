"""Run Ferengi enrichment locally using thread-pool workers (no RabbitMQ required).

Usage:
  python scripts/run_local_enricher.py --workers 6 --batch-size 200 --db outputs/ferengi_enrichment.db
"""
from pathlib import Path
import sys
import os
from dotenv import load_dotenv
import argparse


def main():
    # load .env if present
    env_path = Path('.') / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=int(os.getenv('ENRICH_WORKERS', '4')))
    parser.add_argument('--batch-size', type=int, default=100)
    parser.add_argument('--db', default=os.getenv('FERENGI_DB', 'outputs/ferengi_enrichment.db'))
    args = parser.parse_args()

    from ferengi_full_enrichment import FerengiFullDatabaseEnrichment

    enricher = FerengiFullDatabaseEnrichment(db_path=args.db, workers=args.workers)
    print(f"Starting local enricher: db={args.db} workers={args.workers} batch_size={args.batch_size}")
    success = enricher.run_full_enrichment(batch_size=args.batch_size)
    if success:
        print("Local enrichment run completed successfully")
    else:
        print("Local enrichment run did not complete")


if __name__ == '__main__':
    main()
