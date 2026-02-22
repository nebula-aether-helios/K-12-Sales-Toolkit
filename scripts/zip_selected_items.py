#!/usr/bin/env python3
"""Zip a selected list of top-level items and remove originals if possible.
This script is interactive-safe: it reports failures and leaves items in place if removal fails.
"""
import os
import zipfile
import shutil
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# User-specified targets to archive
TARGETS = ['.devcontainer', '.pytest_cache', '.venv']

present = [t for t in TARGETS if os.path.exists(os.path.join(ROOT, t))]
if not present:
    print('No specified targets present to archive:', TARGETS)
    raise SystemExit(0)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
archive = os.path.join(ROOT, f'ARCHIVE_selected_{timestamp}.zip')

with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    for item in present:
        path = os.path.join(ROOT, item)
        if os.path.isdir(path):
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    arcname = os.path.relpath(fp, ROOT)
                    try:
                        z.write(fp, arcname)
                    except Exception as e:
                        print('Failed to add', fp, e)
        else:
            try:
                z.write(path, os.path.relpath(path, ROOT))
            except Exception as e:
                print('Failed to add', path, e)

print('Created archive:', archive)

# Attempt to remove originals
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

print('\nDone. No git commit performed.')
