#!/usr/bin/env python3
"""Generate a concise report of which fields were enriched, counts, and sample values.
"""
import sqlite3
import sys
import os

db = 'outputs/ferengi_enrichment.db'
if len(sys.argv) > 1:
    db = sys.argv[1]

db = os.path.abspath(db)
conn = sqlite3.connect(db)
cur = conn.cursor()

cur.execute("PRAGMA table_info(contractors)")
cols = [r[1] for r in cur.fetchall()]

# base columns we consider original (keep short but practical)
base_cols = set(['_id','mongo_tag','data_source','market','record_version','record_created_at','record_updated_at','license_number','business_name','dba_name','business_type','classifications','contact_name','contact_type','contact_title','phone_business','address_street','address_city','address_state','address_county','address_zip','status_primary','status_secondary','license_issue_date','license_expiration_date','license_reissue_date'])

patterns = {
    'Google Places': lambda c: c.startswith('gp_'),
    'OSHA/DCA': lambda c: c.startswith('osha_'),
    'Permits/ArcGIS': lambda c: c.startswith('permit_') or c.startswith('permit'),
    'Craigslist': lambda c: c.startswith('cl_'),
    'OSINT': lambda c: c.startswith('osint_'),
    'Court Records': lambda c: c.startswith('court_'),
    'Triggers/Reports': lambda c: c.startswith('trigger_') or c.startswith('report_') or c.startswith('crm_')
}

def detect_source(col):
    for src, fn in patterns.items():
        try:
            if fn(col):
                return src
        except Exception:
            continue
    return 'Other'

report = []
for c in cols:
    if c in base_cols:
        continue
    src = detect_source(c)
    # count non-null / not empty
    try:
        cur.execute(f"SELECT COUNT(*) FROM contractors WHERE {c} IS NOT NULL AND {c} != ''")
        non_null = cur.fetchone()[0]
    except Exception:
        non_null = None

    samples = []
    try:
        cur.execute(f"SELECT {c}, COUNT(*) as cnt FROM contractors WHERE {c} IS NOT NULL GROUP BY {c} ORDER BY cnt DESC LIMIT 5")
        for r in cur.fetchall():
            val = r[0]
            cnt = r[1]
            samples.append((str(val)[:80], cnt))
    except Exception:
        samples = []

    report.append((c, src, non_null, samples))

conn.close()

print('ENRICHMENT FIELD REPORT\n')
print(f"Database: {db}\n")
for col, src, non_null, samples in sorted(report, key=lambda x: (-(x[2] or 0), x[0])):
    print(f"{col}\n  Source: {src}\n  Non-null count: {non_null}\n  Top samples:")
    if samples:
        for s, cnt in samples:
            print(f"    {s!r} — {cnt}")
    else:
        print("    (no sample values available)")
    print()
