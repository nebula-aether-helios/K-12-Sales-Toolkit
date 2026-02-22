#!/usr/bin/env python3
import sqlite3
import json
from pprint import pprint

DB = 'outputs/ferengi_enrichment.db'
conn = sqlite3.connect(DB)
cur = conn.cursor()

# schema
cur.execute("PRAGMA table_info(contractors)")
cols = [r[1] for r in cur.fetchall()]

# overall counts
cur.execute("SELECT COUNT(*) FROM contractors")
total = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM contractors WHERE enrich_status = 'completed'")
completed = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM contractors WHERE enrich_status = 'pending' OR enrich_status IS NULL")
pending = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM contractors WHERE enrich_status = 'error' OR (error_message IS NOT NULL AND TRIM(error_message) <> '')")
errors = cur.fetchone()[0]

# top error messages
cur.execute("SELECT error_message, COUNT(*) as c FROM contractors WHERE error_message IS NOT NULL GROUP BY error_message ORDER BY c DESC LIMIT 10")
top_errors = cur.fetchall()

# sample completed rows
fields = [
    'license_number','business_name','address_city','enrich_status','record_updated_at',
    'gp_place_id','gp_website','gp_rating','gp_review_count','gp_phone_verified','gp_lat','gp_lng',
    'osha_inspection_count','osha_violation_count','osha_penalty_total','osha_last_inspection_date',
    'cl_ad_found','cl_ad_url','cl_enriched_at',
    'trigger_fear_osha_investigation','trigger_envy_market_position','trigger_envy_competitor_permits','error_message'
]
# ensure selected fields exist
sel_fields = [f for f in fields if f in cols]
query = f"SELECT {', '.join(sel_fields)} FROM contractors WHERE enrich_status = 'completed' LIMIT 20"
cur.execute(query)
samples = cur.fetchall()

conn.close()

print('\nCONTRACTORS TABLE COLUMNS:')
print(len(cols), 'columns')
print(', '.join(cols))

print('\nOVERALL COUNTS:')
print('total:', total, 'completed:', completed, 'pending:', pending, 'errors:', errors)

print('\nTOP ERROR MESSAGES:')
for em, c in top_errors:
    print(c, em[:200].replace('\n',' '))

print('\nSAMPLE COMPLETED ROWS (showing fields):')
print(sel_fields)
for row in samples:
    # print as JSON per row
    d = dict(zip(sel_fields, row))
    print(json.dumps(d, default=str))

print('\nDone.')
