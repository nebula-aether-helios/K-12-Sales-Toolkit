#!/usr/bin/env python3
import sqlite3
licenses=[1000103,1000130,1000283,1001121,1001188,1002883,1003405,1003545,1003672,1003955,1004006,1004055,1004470,1005179,1005398,1005427,1005446,1005616,1005646,1005882]
conn=sqlite3.connect('outputs/ferengi_enrichment.db')
cur=conn.cursor()
placeholders=','.join('?' for _ in licenses)
cur.execute(f"SELECT license_number,enrich_status FROM contractors WHERE license_number IN ({placeholders})",licenses)
rows=cur.fetchall()
conn.close()
print('DB rows for sample:')
for r in rows:
    print(r[0], r[1])
print('\nCounts: total=',len(rows),'completed=',len([r for r in rows if r[1]=='completed']))
