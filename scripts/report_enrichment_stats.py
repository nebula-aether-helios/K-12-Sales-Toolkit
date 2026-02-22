"""Print summary statistics from the enrichment SQLite DB.

Usage: python scripts/report_enrichment_stats.py --db outputs/enrichment.db
"""
import argparse
import sqlite3
from datetime import datetime


def fmt(dt_str):
    try:
        return datetime.fromisoformat(dt_str).isoformat()
    except Exception:
        return dt_str


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default='outputs/enrichment.db')
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    cur = conn.cursor()

    def scalar(q):
        cur.execute(q)
        r = cur.fetchone()
        return r[0] if r else 0

    contractors = scalar('SELECT COUNT(*) FROM contractors')
    results = scalar('SELECT COUNT(*) FROM enrichment_results')
    errors = scalar("SELECT COUNT(*) FROM enrichment_results WHERE success=0 OR error IS NOT NULL")

    print(f"contractors: {contractors}")
    print(f"enrichment_results: {results}")
    print(f"errors: {errors}")

    print('\nper-source counts:')
    cur.execute('SELECT source, COUNT(*) FROM enrichment_results GROUP BY source ORDER BY COUNT(*) DESC')
    for src, ct in cur.fetchall():
        print(f" - {src}: {ct}")

    print('\nrecent samples (up to 5):')
    cur.execute('SELECT contractor_id, source, success, error, fetched_at FROM enrichment_results ORDER BY fetched_at DESC LIMIT 5')
    for r in cur.fetchall():
        cid, src, success, error, fetched_at = r
        print(f"{fetched_at} | contractor={cid} | source={src} | success={success} | error={error}")

    conn.close()


if __name__ == '__main__':
    main()
