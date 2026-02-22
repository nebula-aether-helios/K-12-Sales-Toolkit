#!/usr/bin/env python3
"""Mark rows with error_message as pending so they will be retried by the enricher."""
import sqlite3
import sys
import os

db = 'outputs/ferengi_enrichment.db'
if len(sys.argv) > 1:
    db = sys.argv[1]

db = os.path.abspath(db)
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM contractors WHERE error_message IS NOT NULL")
total = cur.fetchone()[0]
cur.execute("UPDATE contractors SET enrich_status='pending' WHERE error_message IS NOT NULL")
conn.commit()
print(f"Marked {cur.rowcount} rows pending (previously had error_message). Total errored: {total}")
conn.close()
