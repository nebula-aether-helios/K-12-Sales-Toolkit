#!/usr/bin/env python3
"""Run a small smoke enrichment batch (limit N) to validate fixes without looping full DB."""
import sqlite3
import sys
import os
# ensure repo root is on sys.path for local imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ferengi_full_enrichment import FerengiFullDatabaseEnrichment
from pathlib import Path
from dotenv import load_dotenv

# load local .env so API keys are available to this script
env_path = Path('.') / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

db = 'outputs/ferengi_enrichment.db'
limit = 5
if len(sys.argv) > 1:
    db = sys.argv[1]
if len(sys.argv) > 2:
    try:
        limit = int(sys.argv[2])
    except Exception:
        pass

print(f"Smoke enrich: db={db} limit={limit}")
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT license_number, business_name, address_city FROM contractors WHERE enrich_status != 'completed' OR enrich_status IS NULL LIMIT ?", (limit,))
rows = cur.fetchall()
conn.close()

if not rows:
    print('No pending rows found for smoke test')
    sys.exit(0)

runner = FerengiFullDatabaseEnrichment(db_path=db, workers=2)

for lic, name, city in rows:
    prospect = {'license_number': lic, 'business_name': name, 'address_city': city}
    print('Enriching', lic, name)
    res = runner.enrich_single_prospect(prospect)
    print('Result status:', res.get('enrich_status'), 'errors:', res.get('error_message'))
    runner.update_database(res)

print('Smoke batch complete. Updated DB for', len(rows), 'rows')
