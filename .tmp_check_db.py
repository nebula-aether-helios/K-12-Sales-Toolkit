import sqlite3,sys
DB='outputs/ferengi_enrichment.db'
try:
    conn=sqlite3.connect(DB)
    cur=conn.cursor()
    cur.execute('SELECT COUNT(*) FROM contractors')
    total=cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM contractors WHERE enrich_status='completed'")
    completed=cur.fetchone()[0]
    cur.execute('SELECT COUNT(DISTINCT license_number) FROM contractors')
    unique_lic=cur.fetchone()[0]
    cur.execute('SELECT license_number, COUNT(*) c FROM contractors GROUP BY license_number HAVING c>1 ORDER BY c DESC LIMIT 20')
    dups=cur.fetchall()
    print('DB:',DB)
    print('total_rows=',total)
    print('completed=',completed)
    print('distinct_license_numbers=',unique_lic)
    print('duplicates_sample=',dups)
    conn.close()
except Exception as e:
    print('ERROR',e)
    sys.exit(1)
