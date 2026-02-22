#!/usr/bin/env python3
import importlib
import os
import sys
# ensure repo root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
print('Checking connector availability and environment keys')
mods = ['v3_enhanced_enrichment', 'connectors.recondon_craigslist']
for m in mods:
    try:
        importlib.import_module(m)
        print(f'Module {m}: AVAILABLE')
    except Exception as e:
        print(f'Module {m}: MISSING ({e})')

keys = ['GOOGLE_PLACES_API_KEY', 'DCA_API', 'US_DEPT_OF_LABOR_API', 'WAYBACK_BASE']
for k in keys:
    print(f'{k}:', 'SET' if os.getenv(k) else 'MISSING')
