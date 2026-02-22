#!/usr/bin/env python3
"""Safe reset of enrichment flags in the contractors table.
Only updates columns that exist in the schema (no schema changes).
"""
import sqlite3
import sys
from pathlib import Path

def main(db_path):
    db = Path(db_path)
    if not db.exists():
        print('DB not found:', db_path)
        return 2
    conn = sqlite3.connect(str(db))
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(contractors)")
    cols = [r[1] for r in cur.fetchall()]
    # target columns and desired reset values
    resets = {
        'enrich_status': "'pending'",
        'enrich_google_places_done': '0',
        'enrich_osha_done': '0',
        'enrich_permits_done': '0',
        'enrich_craigslist_done': '0',
        'enrich_osint_done': '0',
        'enrich_court_records_done': '0',
        'gp_place_id': 'NULL',
        'gp_website': 'NULL',
        'gp_rating': 'NULL',
        'gp_review_count': 'NULL',
        'gp_phone_verified': 'NULL',
        'gp_hours': 'NULL',
        'gp_lat': 'NULL',
        'gp_lng': 'NULL',
        'gp_enriched_at': 'NULL',
        'osha_inspection_count': 'NULL',
        'osha_violation_count': 'NULL',
        'osha_penalty_total': 'NULL',
        'osha_last_inspection_date': 'NULL',
        'osha_open_cases': 'NULL',
        'osha_serious_violations': 'NULL',
        'osha_enriched_at': 'NULL',
        'permit_active_count': 'NULL',
        'permit_total_value': 'NULL',
        'permit_last_issued_date': 'NULL',
        'permit_enriched_at': 'NULL',
        'cl_ad_found': '0',
        'cl_ad_url': 'NULL',
        'cl_license_displayed': '0',
        'cl_down_payment_violation': '0',
        'cl_enriched_at': 'NULL',
        'osint_email_discovered': 'NULL',
        'osint_email_verified': 'NULL',
        'osint_cell_phone': 'NULL',
        'osint_enriched_at': 'NULL',
        'error_message': 'NULL'
    }
    set_parts = []
    for c, v in resets.items():
        if c in cols:
            set_parts.append(f"{c} = {v}")
    if not set_parts:
        print('No known enrichment columns found to reset. Columns present:', cols)
        return 1
    sql = f"UPDATE contractors SET {', '.join(set_parts)} WHERE 1"
    print('Executing:', sql[:200])
    cur.execute(sql)
    conn.commit()
    cur.execute('SELECT COUNT(*) FROM contractors')
    total = cur.fetchone()[0]
    print('Reset enrichment flags for', total, 'rows')
    conn.close()
    return 0

if __name__ == '__main__':
    db = sys.argv[1] if len(sys.argv) > 1 else 'outputs/ferengi_enrichment.db'
    sys.exit(main(db))
