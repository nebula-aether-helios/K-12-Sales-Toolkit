#!/usr/bin/env python3
# Verify that DCA/OSHA sources are discoverable from catalog manifests and report findings
import json
from pathlib import Path
out = {'manifests': [], 'found_local_example_files': 0}
src = Path('catalog_api') / 'sources'
if not src.exists():
    out['error'] = 'catalog_api/sources not found'
else:
    for p in src.glob('*.json'):
        try:
            j = json.loads(p.read_text(encoding='utf-8'))
        except Exception as e:
            out['manifests'].append({'path': str(p), 'error': str(e)})
            continue
        ef = j.get('example_files') or []
        files_exist = []
        for f in ef:
            fp = Path(f)
            if not fp.exists():
                fp = Path(f.lstrip('/'))
            files_exist.append({'file': f, 'exists': fp.exists(), 'resolved': str(fp)})
            if fp.exists():
                out['found_local_example_files'] += 1
        out['manifests'].append({'path': str(p), 'title': j.get('title'), 'example_files': files_exist})

out_path = Path('outputs') / 'dca_manifest_report.json'
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(out, indent=2), encoding='utf-8')
print('Wrote', out_path)