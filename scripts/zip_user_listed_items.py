#!/usr/bin/env python3
"""Zip the exact list of items specified by the user and attempt to remove originals.
This will not make any git commits. It will report failures to remove items (permissions).
"""
import os
import zipfile
import shutil
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# User-provided list (top-level and specific files)
TARGETS = [
    '.github',
    '.github/workflows',
    '.github/workflows/ci.yml',
    '.pytest_cache',
    '.venv',
    '.venv/Include',
    '.venv/Lib',
    '.venv/Scripts',
    '.venv/.gitignore',
    '.venv/pyvenv.cfg',
    '.vscode',
    'catalog_api',
    'catalog_api/__pycache__',
    'catalog_api/fetchers',
    'catalog_api/integrations',
    'catalog_api/sources',
    'catalog_api/sources/ca_la_accessors_manifest.json',
    'catalog_api/sources/county_of_los_angeles_open_data.json',
    'catalog_api/sources/dca_manifest.json',
    'catalog_api/sources/la_city_geohub.json',
    'catalog_api/sources/osha_github_manifest.json',
    'catalog_api/sources/PLAN',
    'catalog_api/sources/sacramento_cslb_manifest.json',
    'catalog_api/tests',
    'catalog_api/__init__.py',
    'catalog_api/ai_client.py',
    'catalog_api/cli.py',
    'catalog_api/config.py',
    'catalog_api/gemini_integration.md',
    'catalog_api/ingest.py',
    'catalog_api/main.py',
    'catalog_api/models.py',
    'catalog_api/README_CLI.md',
    'catalog_api/README.md',
    'catalog_api/runner.py',
    'catalog_api/storage.py',
    'catalog_api/TODO.md',
    'catalog_api/utils.py',
    'connectors',
    'outputs',
    'scripts',
    'scripts/__pycache__',
    'scripts/analyze_enrichment_run.py',
    'scripts/batch_debug_errors.py',
    # ... include rest of scripts or just zip the whole scripts dir above
    'src',
    'tests',
    '.env',
    '.gitignore'
]

present = [p for p in TARGETS if os.path.exists(os.path.join(ROOT, p))]
if not present:
    print('No listed targets exist in repo root; nothing to do.')
    raise SystemExit(0)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
archive = os.path.join(ROOT, f'ARCHIVE_user_listed_{timestamp}.zip')

with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    for item in present:
        path = os.path.join(ROOT, item)
        if os.path.isdir(path):
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    arcname = os.path.relpath(fp, ROOT)
                    try:
                        zf.write(fp, arcname)
                    except Exception as e:
                        print('Failed to add', fp, e)
        else:
            try:
                zf.write(path, os.path.relpath(path, ROOT))
            except Exception as e:
                print('Failed to add', path, e)

print('Archive created:', archive)

# Attempt removal
for item in present:
    path = os.path.join(ROOT, item)
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
            print('Removed', path)
        else:
            os.remove(path)
            print('Removed', path)
    except Exception as e:
        print('Could not remove', path, '-', e)

print('Done. No git commit was made.')
