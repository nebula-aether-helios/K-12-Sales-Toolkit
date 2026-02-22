#!/usr/bin/env python3
import sqlite3
conn=sqlite3.connect('outputs/ferengi_enrichment.db')
cur=conn.cursor()
cur.execute("SELECT license_number, business_name, enrich_status, error_message FROM contractors WHERE enrich_status='error' LIMIT 20")
rows=cur.fetchall()
for r in rows:
    ln, name, status, em = r
    print(f"{ln}\t{name}\t{status}\t{(em[:200].replace('\n',' ') if em else '')}")
conn.close()
