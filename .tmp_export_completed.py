import sqlite3, csv
DB='outputs/ferengi_enrichment.db'
cols=[
    'license_number','business_name','enrich_status','record_updated_at',
    'gp_place_id','gp_website','gp_rating','gp_review_count','gp_enriched_at',
    'cl_ad_found','cl_license_displayed','cl_enriched_at',
    'osha_inspection_count','osha_violation_count','osha_penalty_total','osha_enriched_at',
    'derived_domain','domain_has_mx','mx_records','dns_score','osint_email_discovered','osint_enriched_at',
    'phone_business','phone_valid','phone_type','phone_region',
    'dd_dorks','dd_result',
    'trigger_fear_osha_investigation','trigger_fear_craigslist_violation','trigger_envy_market_position'
]
conn=sqlite3.connect(DB)
cur=conn.cursor()
q = 'SELECT ' + ','.join(cols) + " FROM contractors WHERE enrich_status='completed' LIMIT 1000"
try:
    cur.execute(q)
except Exception as e:
    print('QUERY ERROR', e)
    # fallback: select all columns
    cur.execute("SELECT * FROM contractors WHERE enrich_status='completed'")
    cols = [d[0] for d in cur.description]
rows = cur.fetchall()
conn.close()
out='outputs/completed_enriched_rows.csv'
with open(out,'w',newline='',encoding='utf-8') as fh:
    w=csv.writer(fh)
    w.writerow(cols)
    for r in rows:
        w.writerow([str(x) if x is not None else '' for x in r])
print('WROTE', out, 'ROWS', len(rows))
