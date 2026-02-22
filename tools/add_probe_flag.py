#!/usr/bin/env python3
"""Add probe_in_progress column to enriched_prospects for SQLite DB if missing."""
import sqlite3
import sys
import argparse

p = argparse.ArgumentParser()
p.add_argument('--db', required=True)
args = p.parse_args()

db = args.db
# expect sqlite:///path or sqlite:///<abs>
if db.startswith('sqlite:///'):
    path = db.replace('sqlite:///', '')
else:
    path = db
conn = sqlite3.connect(path)
cur = conn.cursor()
# check if column exists
cur.execute("PRAGMA table_info(enriched_prospects)")
cols = [r[1] for r in cur.fetchall()]
if 'probe_in_progress' in cols:
    print('Column probe_in_progress already exists')
    sys.exit(0)
try:
    cur.execute("ALTER TABLE enriched_prospects ADD COLUMN probe_in_progress BOOLEAN DEFAULT 0")
    conn.commit()
    print('Added probe_in_progress column')
except Exception as e:
    print('Failed to add column:', e)
    sys.exit(2)
finally:
    conn.close()
