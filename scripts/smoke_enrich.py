#!/usr/bin/env python3
"""Run a single-batch smoke enrichment to validate fixes and record HTTP evidence.

Usage:
  # PowerShell
  $env:RECORD_HTTP='1'; python scripts/smoke_enrich.py --batch-size 200 --db outputs/ferengi_enrichment.db
"""
from pathlib import Path
import sys
import os
from dotenv import load_dotenv
import argparse
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed


def main():
    env_path = Path('.') / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    parser = argparse.ArgumentParser()
    parser.add_argument('--batch-size', type=int, default=200)
    parser.add_argument('--workers', type=int, default=int(os.getenv('ENRICH_WORKERS','4')))
    parser.add_argument('--db', default=os.getenv('FERENGI_DB','outputs/ferengi_enrichment.db'))
    args = parser.parse_args()

    from ferengi_full_enrichment import FerengiFullDatabaseEnrichment

    enricher = FerengiFullDatabaseEnrichment(db_path=args.db, workers=args.workers)

    # Select a single batch of pending prospects
    conn = sqlite3.connect(args.db)
    query = """
        SELECT license_number, business_name, address_city
        FROM contractors
        WHERE enrich_status != 'completed' OR enrich_status IS NULL
        LIMIT ?
    """
    import pandas as pd
    df = pd.read_sql_query(query, conn, params=(args.batch_size,))
    conn.close()

    prospects = df.to_dict('records')
    print(f"Selected {len(prospects)} prospects for smoke enrichment")

    total_processed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        future_to_prospect = {ex.submit(enricher.enrich_single_prospect, p): p for p in prospects}
        for fut in as_completed(future_to_prospect):
            prospect = future_to_prospect[fut]
            try:
                enrichment_result = fut.result()
            except Exception as e:
                print('Worker failed for', prospect.get('license_number'), e)
                continue

            enricher.update_database(enrichment_result)
            total_processed += 1
            if total_processed % 10 == 0:
                print(f"Processed {total_processed} records")

    print('Smoke enrichment complete. Processed', total_processed)


if __name__ == '__main__':
    main()
