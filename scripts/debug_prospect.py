#!/usr/bin/env python3
"""Debug a single prospect by running enrich_single_prospect and printing tracebacks.
Usage: python scripts/debug_prospect.py <license_number>
"""
import sys
from pathlib import Path
import os
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python scripts/debug_prospect.py <license_number>')
        raise SystemExit(1)
    lic = sys.argv[1]

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    import sqlite3, traceback
    from ferengi_full_enrichment import FerengiFullDatabaseEnrichment

    db = os.environ.get('FERENGI_DB', 'outputs/ferengi_enrichment.db')
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute('SELECT * FROM contractors WHERE license_number = ?', (lic,))
    row = cur.fetchone()
    if not row:
        print('License not found:', lic)
        raise SystemExit(1)
    cols = [d[0] for d in cur.description]
    prospect = dict(zip(cols, row))
    conn.close()

    enricher = FerengiFullDatabaseEnrichment(db_path=db)
    try:
        res = enricher.enrich_single_prospect(prospect)
        print('Result:')
        print(res)
    except Exception:
        print('Exception during enrich:')
        traceback.print_exc()
