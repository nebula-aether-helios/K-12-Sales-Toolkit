#!/usr/bin/env python3
import sqlite3
DB='outputs/ferengi_enrichment.db'
conn=sqlite3.connect(DB)
cur=conn.cursor()
cur.execute("UPDATE contractors SET error_message = NULL WHERE enrich_status = 'completed'")
updated=conn.total_changes
conn.commit()
conn.close()
print('Cleared error_message for', updated, 'rows')
