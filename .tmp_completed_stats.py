import sqlite3
DB='outputs/ferengi_enrichment.db'
conn=sqlite3.connect(DB)
cur=conn.cursor()
metrics=['enrich_google_places_done','enrich_osha_done','enrich_permits_done','enrich_craigslist_done','enrich_osint_done']
for m in metrics:
    try:
        cur.execute(f"SELECT COUNT(*) FROM contractors WHERE enrich_status='completed' AND {m}=1")
        c=cur.fetchone()[0]
    except Exception as e:
        c='ERR'
    print(m, c)
cur.execute("SELECT COUNT(*) FROM contractors WHERE enrich_status='completed'")
print('total_completed', cur.fetchone()[0])
conn.close()
