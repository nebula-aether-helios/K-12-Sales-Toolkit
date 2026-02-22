#!/usr/bin/env python3
"""Find rows with NULL or missing numeric fields and export CSVs for reprocessing.
"""
import sqlite3
import csv
from pathlib import Path
import json

OUT = Path('outputs')
OUT.mkdir(exist_ok=True)
DB = Path('outputs/ferengi_enrichment.db')

if not DB.exists():
    print('DB not found:', DB)
    raise SystemExit(1)

conn = sqlite3.connect(str(DB))
cur = conn.cursor()

queries = {
    'gp_rating_nulls': "SELECT license_number,business_name,gp_rating,enrich_status,error_message FROM contractors WHERE gp_rating IS NULL OR TRIM(COALESCE(gp_rating,'')) = ''",
    'risk_permit_nulls': "SELECT license_number,business_name,risk_score,permit_total_value,enrich_status,error_message FROM contractors WHERE risk_score IS NULL OR permit_total_value IS NULL",
    'combined_nulls': "SELECT license_number,business_name,gp_rating,risk_score,permit_total_value,enrich_status,error_message FROM contractors WHERE gp_rating IS NULL OR risk_score IS NULL OR permit_total_value IS NULL",
    'error_rows': "SELECT license_number,business_name,error_message FROM contractors WHERE error_message IS NOT NULL"
}

results = {}
for name, q in queries.items():
    cur.execute(q)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    results[name + '_count'] = len(rows)
    csv_path = OUT / f'{name}.csv'
    with open(csv_path, 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in rows:
            w.writerow([ (x if x is not None else '') for x in r])
    results[name + '_csv'] = str(csv_path)
    print(f'Wrote {len(rows)} rows to', csv_path)

# summary counts
summary_path = OUT / 'problematic_null_counts.json'
summary = {
    'db_path': str(DB),
    'generated_at': str( Path().cwd() ),
}
summary.update(results)
with open(summary_path, 'w', encoding='utf-8') as fh:
    json.dump(summary, fh, indent=2)

print('Summary written to', summary_path)
conn.close()
