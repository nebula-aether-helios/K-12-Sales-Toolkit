#!/usr/bin/env python3
"""Run enrich_single_prospect for the first N error rows to capture exceptions.
"""
import sqlite3
import traceback
import sys, os
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
from ferengi_full_enrichment import FerengiFullDatabaseEnrichment

DB='outputs/ferengi_enrichment.db'
conn=sqlite3.connect(DB)
cur=conn.cursor()
cur.execute("SELECT license_number FROM contractors WHERE enrich_status='error' LIMIT 10")
rows=cur.fetchall()
conn.close()

enricher=FerengiFullDatabaseEnrichment(db_path=DB)
for (lic,) in rows:
    try:
        # fetch row
        conn=sqlite3.connect(DB)
        cur=conn.cursor()
        cur.execute('SELECT * FROM contractors WHERE license_number=?',(lic,))
        r=cur.fetchone()
        cols=[d[0] for d in cur.description]
        prospect=dict(zip(cols,r))
        conn.close()

        res=enricher.enrich_single_prospect(prospect)
        print('===',lic,'RESULT===')
        print(res)
    except Exception:
        print('===',lic,'EXCEPTION===')
        traceback.print_exc()
