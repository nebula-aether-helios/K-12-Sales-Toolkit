"""Basic CKAN fetcher helpers for package/resource metadata and preview.
"""
from typing import List, Dict, Any
import httpx


def _api_base(site_base: str) -> str:
    return site_base.rstrip('/') + '/api/3/action'


def fetch_metadata(site_base: str, package_id: str) -> Dict[str, Any]:
    api = _api_base(site_base)
    try:
        r = httpx.get(f"{api}/package_show", params={'id': package_id}, timeout=20.0)
        if r.status_code != 200:
            return {'title': None, 'description': None, 'raw': {'error': r.text}}
        j = r.json()
        result = j.get('result') or {}
        title = result.get('title')
        desc = result.get('notes')
        resources = result.get('resources', [])
        schema = [{'name': r.get('name'), 'format': r.get('format')} for r in resources]
        return {'title': title, 'description': desc, 'schema': schema, 'raw': result}
    except Exception as e:
        return {'title': None, 'description': None, 'raw': {'error': str(e)}}


def fetch_preview(site_base: str, package_id: str, n: int = 10) -> List[Dict[str, Any]]:
    # try to get first CSV resource and fetch its download_url
    api = _api_base(site_base)
    try:
        r = httpx.get(f"{api}/package_show", params={'id': package_id}, timeout=20.0)
        if r.status_code != 200:
            return []
        j = r.json()
        result = j.get('result') or {}
        resources = result.get('resources', [])
        for res in resources:
            fmt = (res.get('format') or '').lower()
            url = res.get('url') or res.get('download_url')
            if fmt in ('csv', 'json', 'geojson') and url:
                try:
                    rr = httpx.get(url, timeout=20.0)
                    if rr.status_code != 200:
                        continue
                    if fmt == 'csv':
                        # simple CSV parsing
                        text = rr.text.splitlines()
                        rows = [line.split(',') for line in text[1:1+n]]
                        return rows
                    else:
                        return rr.json()[:n]
                except Exception:
                    continue
        return []
    except Exception:
        return []
"""Basic CKAN fetcher placeholders."""
from typing import List, Dict, Any
import httpx


def fetch_metadata(site_base: str, dataset_identifier: str) -> Dict[str, Any]:
    # CKAN API: /api/3/action/package_show?id={id}
    url = site_base.rstrip('/') + '/api/3/action/package_show'
    r = httpx.get(url, params={'id': dataset_identifier}, timeout=20.0)
    if r.status_code != 200:
        return {'title': None, 'description': None, 'raw': {'error': r.text}}
    j = r.json()
    result = j.get('result', {})
    return {
        'title': result.get('title'),
        'description': result.get('notes'),
        'schema': result.get('resources', []),
        'source_url': result.get('url') or site_base,
        'raw': result,
    }


def fetch_preview(site_base: str, dataset_identifier: str, n: int = 10) -> List[Dict[str, Any]]:
    # CKAN resources may have direct URLs; this is a best-effort placeholder.
    meta = fetch_metadata(site_base, dataset_identifier)
    resources = meta.get('schema') or []
    for r in resources:
        if r.get('format','').lower() in ['csv', 'json'] and r.get('url'):
            try:
                rr = httpx.get(r['url'], timeout=20.0)
                if rr.status_code == 200:
                    # naive CSV/JSON handling omitted for brevity
                    return []
            except Exception:
                continue
    return []
