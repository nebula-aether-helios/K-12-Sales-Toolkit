import sqlite3,csv,sys
conn=sqlite3.connect('outputs/ferengi_enrichment.db')
cur=conn.cursor()
cur.execute('SELECT license_number,business_name,address_city,enrich_status,error_message FROM contractors WHERE error_message IS NOT NULL')
rows=cur.fetchall()
with open('outputs/errored_rows_export.csv','w',newline='',encoding='utf-8') as fh:
    w=csv.writer(fh)
    w.writerow(['license_number','business_name','address_city','enrich_status','error_message'])
    w.writerows(rows)
conn.close()
print('Wrote outputs/errored_rows_export.csv', len(rows))
