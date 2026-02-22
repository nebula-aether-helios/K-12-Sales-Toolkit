#!/usr/bin/env python3
"""Restore selected top-level entries from a ZIP archive into repo root.
Usage: python scripts/restore_from_archive.py <archive.zip> item1 item2 ...
"""
import sys
import os
import zipfile

if len(sys.argv) < 3:
    print('Usage: restore_from_archive.py <archive.zip> item1 item2 ...')
    sys.exit(1)

archive = sys.argv[1]
items = sys.argv[2:]
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

if not os.path.exists(archive):
    # try root
    archive = os.path.join(ROOT, archive)
    if not os.path.exists(archive):
        print('Archive not found:', sys.argv[1])
        sys.exit(2)

print('Restoring from', archive, 'items:', items)
with zipfile.ZipFile(archive, 'r') as zf:
    names = zf.namelist()
    for item in items:
        # extract all entries that start with item + '/'
        prefix = item.rstrip('/') + '/'
        matched = [n for n in names if n.startswith(prefix) or n == item]
        if not matched:
            print('No entries for', item)
            continue
        for name in matched:
            dest = os.path.join(ROOT, name)
            destdir = os.path.dirname(dest)
            if not os.path.exists(destdir):
                os.makedirs(destdir, exist_ok=True)
            try:
                with zf.open(name) as src, open(dest, 'wb') as dst:
                    dst.write(src.read())
            except IsADirectoryError:
                # skip directories
                pass
        print('Restored', item)
print('Done.')
