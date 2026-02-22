#!/usr/bin/env python3
"""Run a smoke enrichment pass specifically for rows that previously errored, capturing full tracebacks.
"""
import sqlite3
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ferengi_full_enrichment import FerengiFullDatabaseEnrichment
from pathlib import Path
from dotenv import load_dotenv

# load local .env so API keys are available to this script
env_path = Path('.') / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

DB = 'outputs/ferengi_enrichment.db'
LIMIT = 20
if len(sys.argv) > 1:
    DB = sys.argv[1]
if len(sys.argv) > 2:
    try:
        LIMIT = int(sys.argv[2])
    except Exception:
        pass

print(f"Smoke enrich (errored rows): db={DB} limit={LIMIT}")
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT license_number, business_name, address_city FROM contractors WHERE error_message IS NOT NULL AND TRIM(error_message)<>'' LIMIT ?", (LIMIT,))
rows = cur.fetchall()
conn.close()

if not rows:
    print('No errored rows found for smoke test')
    sys.exit(0)

runner = FerengiFullDatabaseEnrichment(db_path=DB, workers=2)

for lic, name, city in rows:
    prospect = {'license_number': lic, 'business_name': name, 'address_city': city}
    print('\n--- Enriching', lic, name)
    res = runner.enrich_single_prospect(prospect)
    status = res.get('enrich_status')
    print('Result status:', status)
    if status == 'error':
        print('Captured traceback:\n', res.get('error_message'))
    runner.update_database(res)

print('\nSmoke batch complete. Updated DB for', len(rows), 'rows')
