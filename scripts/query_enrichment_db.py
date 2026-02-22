#!/usr/bin/env python3
import sqlite3
import sys

db='outputs/ferengi_enrichment.db'
if len(sys.argv)>1:
    db=sys.argv[1]

conn=sqlite3.connect(db)
c=conn.cursor()
try:
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables=[r[0] for r in c.fetchall()]
    print('Tables:', tables)
    if 'contractors' in tables:
        c.execute('PRAGMA table_info(contractors)')
        cols=[r[1] for r in c.fetchall()]
        print('contractors columns:', cols)
        try:
            c.execute("SELECT enrich_status, COUNT(*) FROM contractors GROUP BY enrich_status")
            print('Counts by enrich_status:')
            for r in c.fetchall():
                print(r)
        except Exception as e:
            print('count by enrich_status failed:', e)
        try:
            c.execute("SELECT COUNT(*) FROM contractors WHERE error_message IS NOT NULL")
            err_count = c.fetchone()[0]
            print('\nRows with error_message not null:', err_count)
        except Exception as e:
            print('error_message count failed:', e)
        try:
            print('\nTop error messages:')
            c.execute("SELECT error_message, COUNT(*) as c FROM contractors WHERE error_message IS NOT NULL GROUP BY error_message ORDER BY c DESC LIMIT 20")
            for r in c.fetchall():
                print(r)
        except Exception as e:
            print('top error messages failed:', e)
        try:
            c.execute("SELECT license_number, enrich_status, error_message FROM contractors WHERE error_message IS NOT NULL LIMIT 20")
            rows=c.fetchall()
            print('\nSample error rows:')
            for r in rows:
                print(r)
        except Exception as e:
            print('sample error query failed:', e)
    else:
        print('contractors table not found; showing first 10 rows of first table if any')
        if tables:
            t=tables[0]
            c.execute(f'SELECT * FROM {t} LIMIT 10')
            for r in c.fetchall():
                print(r)
except Exception as e:
    print('DB access failed:', e)
finally:
    conn.close()
