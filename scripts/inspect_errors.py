#!/usr/bin/env python3
import sqlite3, sys
db='outputs/ferengi_enrichment.db'
if len(sys.argv)>1:
    db=sys.argv[1]

conn=sqlite3.connect(db)
c=conn.cursor()
print('Rows with non-null error_message:')
for row in c.execute("SELECT error_message, COUNT(*) FROM contractors WHERE error_message IS NOT NULL GROUP BY error_message ORDER BY COUNT(*) DESC"):
    print(row)
print('\nSample rows for the top error:\n')
for r in c.execute("SELECT license_number, enrich_status, error_message FROM contractors WHERE error_message IS NOT NULL ORDER BY error_message DESC LIMIT 100"):
    print(r)
conn.close()
