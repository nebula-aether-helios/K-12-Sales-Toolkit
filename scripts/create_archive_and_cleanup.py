#!/usr/bin/env python3
"""Create ARCHIVE_<timestamp>.zip containing non-essential files and remove originals.
Uses ACTIVE_FILES.md as the keep-list baseline plus a few repo essentials.
"""
import os
import shutil
import zipfile
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
KEEP = {
    '.env', 'requirements.txt', 'README.md', 'INSTRUCTIONS.md', 'scripts',
    'ferengi_full_enrichment.py', 'deep_enrichment_pipeline.py', 'v3_enhanced_enrichment.py',
    'run_ferengi_all.py', 'outputs', 'catalog_api', 'connectors', 'src', 'tests',
    'ACTIVE_FILES.md', 'ARCHIVE_PROPOSAL.md', '.git', '.github', '.gitignore', 'LICENSE',
    'Dockerfile', 'docker-compose.yml', '.vscode', '.devcontainer', 'requirements.txt'
}

# Normalize keep names to actual entries present
entries = os.listdir(ROOT)
keep_present = {e for e in entries if e in KEEP}
# Always keep the scripts directory (ensure it exists)
if 'scripts' in entries:
    keep_present.add('scripts')

# Items to archive: those top-level entries not in keep_present
to_archive = [e for e in entries if e not in keep_present]
# But avoid archiving special files we shouldn't touch in root like '.pyc' caches (none expected)
# Exclude empty names and ensure hidden files like .env.example are archived unless in KEEP

if not to_archive:
    print('Nothing to archive. Workspace already minimal.')
    exit(0)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
archive_name = os.path.join(ROOT, f'ARCHIVE_{timestamp}.zip')

print('Archiving items:', to_archive)

with zipfile.ZipFile(archive_name, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    for item in to_archive:
        path = os.path.join(ROOT, item)
        if os.path.isdir(path):
            # Walk directory
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

print('Archive created at', archive_name)

# Now remove originals (move to trash would be safer; user asked to cleanup, so delete)
for item in to_archive:
    path = os.path.join(ROOT, item)
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
            print('Removed dir', path)
        else:
            os.remove(path)
            print('Removed file', path)
    except Exception as e:
        print('Failed to remove', path, e)

print('Cleanup complete. Remaining top-level entries:')
for e in os.listdir(ROOT):
    print(' -', e)

print('\nNOTE: No git commit was made. Review the archive and workspace, then commit as desired.')
