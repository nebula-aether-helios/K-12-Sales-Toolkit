#!/usr/bin/env python3
"""Reset completed/errored rows so they can be reprocessed by the enricher.

This script is read-write to the SQLite DB at outputs/ferengi_enrichment.db.
It will:
 - Reset rows marked 'completed' but missing permit_total_value to NULL enrich_status
 - Reset rows with error_message to NULL enrich_status and clear error_message
 - Print counts before and after
"""
from pathlib import Path
import sqlite3
import json

DB = Path('outputs/ferengi_enrichment.db')
if not DB.exists():
    print('DB not found:', DB)
    raise SystemExit(1)

conn = sqlite3.connect(str(DB))
cur = conn.cursor()

def count_pending():
    cur.execute("SELECT COUNT(*) FROM contractors WHERE enrich_status IS NULL")
    return cur.fetchone()[0]

def count_completed_missing_permit():
    cur.execute("SELECT COUNT(*) FROM contractors WHERE enrich_status='completed' AND (permit_total_value IS NULL OR trim(permit_total_value)='')")
    return cur.fetchone()[0]

def count_error_rows():
    cur.execute("SELECT COUNT(*) FROM contractors WHERE error_message IS NOT NULL AND trim(error_message)<>''")
    return cur.fetchone()[0]

print('Before:')
print(' pending rows:', count_pending())
print(' completed but missing permit:', count_completed_missing_permit())
print(' error rows:', count_error_rows())

# 1) Reset completed but missing permit -> make pending and clear certain fields
cur.execute("""
UPDATE contractors
SET enrich_status = NULL,
    error_message = NULL,
    risk_score = NULL,
    permit_total_value = NULL
WHERE enrich_status = 'completed'
  AND (permit_total_value IS NULL OR trim(permit_total_value)='')
""")
conn.commit()

# 2) Reset errored rows
cur.execute("""
UPDATE contractors
SET enrich_status = NULL,
    error_message = NULL
WHERE error_message IS NOT NULL AND trim(error_message)<>''
""")
conn.commit()

print('\nAfter:')
print(' pending rows:', count_pending())
print(' completed but missing permit:', count_completed_missing_permit())
print(' error rows:', count_error_rows())

summary = {
    'db': str(DB),
    'pending_after': count_pending(),
    'completed_missing_permit_after': count_completed_missing_permit(),
    'error_rows_after': count_error_rows()
}

out = Path('outputs') / 'reset_problematic_rows_summary.json'
out.write_text(json.dumps(summary, indent=2), encoding='utf-8')

print('\nWrote summary to', out)
conn.close()
