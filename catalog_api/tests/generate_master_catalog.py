"""Generate a master catalog JSON describing which manifest API calls succeed.

Writes `catalog_api/tests/master_catalog.json` with entries per manifest.
"""
import json
from pathlib import Path
from importlib import import_module
import traceback


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCES_DIR = REPO_ROOT / 'catalog_api' / 'sources'
OUT_PATH = Path(__file__).resolve().parent / 'master_catalog.json'


def load_manifests():
    manifests = []
    for p in SOURCES_DIR.glob('*.json'):
        try:
            manifests.append(json.loads(p.read_text(encoding='utf-8')))
        except Exception:
            continue
    return manifests


def check_manifest(manifest: dict):
    mtype = manifest.get('type') or manifest.get('api_slug') or 'unknown'
    name = manifest.get('name') or manifest.get('api_slug')
    result = {'name': name, 'type': mtype, 'status': 'unknown', 'notes': [], 'metadata': None, 'preview_count': 0}
    try:
        if mtype == 'arcgis' or (manifest.get('api_slug','').startswith('arcgis')):
            from catalog_api.fetchers import arcgis_fetcher
            # try CSV of services
            csv_rel = manifest.get('source_csv')
            if csv_rel:
                csv_path = (SOURCES_DIR / csv_rel)
                if not csv_path.exists():
                    # try repo root / basename as fallback
                    csv_path = (REPO_ROOT / Path(csv_rel).name)
                if csv_path.exists():
                    # read first arcgis url
                    import csv
                    with open(csv_path, newline='', encoding='utf-8') as f:
                        r = csv.DictReader(f)
                        for row in r:
                            url = row.get('url') or row.get('URL') or row.get('link')
                            if url:
                                meta = arcgis_fetcher.fetch_metadata(url)
                                pv = arcgis_fetcher.fetch_preview(url, n=5)
                                result['status'] = 'ok'
                                result['metadata'] = {'title': meta.get('title'), 'schema_len': len(meta.get('schema') or [])}
                                result['preview_count'] = len(pv)
                                break
            else:
                result['status'] = 'no_source_csv'

        elif mtype == 'csv' or (manifest.get('api_slug','').startswith('csv')):
            csv_rel = manifest.get('source_csv')
            if csv_rel:
                csv_path = (SOURCES_DIR / csv_rel)
                if not csv_path.exists():
                    csv_path = (REPO_ROOT / Path(csv_rel).name)
                if csv_path.exists():
                    result['status'] = 'ok'
                    # sample header and rows
                    import csv
                    with open(csv_path, newline='', encoding='utf-8') as f:
                        r = csv.reader(f)
                        rows = []
                        for i,row in enumerate(r):
                            rows.append(row)
                            if i>=5:
                                break
                    result['metadata'] = {'headers': rows[0] if rows else []}
                    result['preview_count'] = max(0, len(rows)-1)
                else:
                    result['status'] = 'csv_missing'
            else:
                result['status'] = 'no_source_csv'

        elif mtype.startswith('github') or manifest.get('type') == 'github':
            from catalog_api.fetchers import github_fetcher
            repo_field = manifest.get('repo')
            repos = []
            if repo_field:
                owner, repo = github_fetcher._owner_repo_from_url(repo_field)
                if owner and not repo:
                    repos = github_fetcher.list_org_repos(repo_field)
                elif owner and repo:
                    repos = [f"{owner}/{repo}"]
            if not repos:
                repos = manifest.get('example_repos', [])
            result['status'] = 'ok' if repos else 'no_repos'
            result['metadata'] = {'repos_count': len(repos), 'repos_sample': repos[:5]}

        else:
            result['status'] = 'unsupported_type'
    except Exception as e:
        result['status'] = 'error'
        result['notes'].append(str(e))
        result['notes'].append(traceback.format_exc())
    return result


def main():
    manifests = load_manifests()
    out = []
    for m in manifests:
        out.append(check_manifest(m))
    OUT_PATH.write_text(json.dumps(out, indent=2), encoding='utf-8')
    print('Wrote master catalog to', OUT_PATH)


if __name__ == '__main__':
    main()
