"""Minimal Socrata fetcher helpers using httpx."""
from typing import List, Dict, Any
import httpx
from ..config import settings


def _build_url(site_base: str, path: str) -> str:
    return site_base.rstrip('/') + '/' + path.lstrip('/')


def fetch_metadata(site_base: str, dataset_identifier: str) -> Dict[str, Any]:
    """Fetch basic metadata for a Socrata dataset view.

    dataset_identifier can be a 4x4 id or a full path fragment.
    """
    client = httpx.Client(timeout=20.0)
    headers = {}
    if settings.SOCRATA_APP_TOKEN:
        headers['X-App-Token'] = settings.SOCRATA_APP_TOKEN
    # Socrata view metadata endpoint
    url = _build_url(site_base, f"api/views/{dataset_identifier}.json")
    r = client.get(url, headers=headers)
    if r.status_code != 200:
        return {"title": None, "description": None, "raw": {"error": r.text}}
    j = r.json()
    schema = []
    for col in j.get('columns', []):
        schema.append({
            'name': col.get('name'),
            'fieldName': col.get('fieldName'),
            'dataTypeName': col.get('dataTypeName'),
            'description': col.get('description'),
        })
    return {
        'title': j.get('name'),
        'description': j.get('description'),
        'schema': schema,
        'source_url': _build_url(site_base, f"d/{dataset_identifier}"),
        'raw': j,
    }


def fetch_preview(site_base: str, dataset_identifier: str, n: int = 10) -> List[Dict[str, Any]]:
    client = httpx.Client(timeout=20.0)
    headers = {}
    if settings.SOCRATA_APP_TOKEN:
        headers['X-App-Token'] = settings.SOCRATA_APP_TOKEN
    # Socrata data endpoint: /resource/{id}.json
    url = _build_url(site_base, f"resource/{dataset_identifier}.json")
    params = {'$limit': n}
    r = client.get(url, headers=headers, params=params)
    if r.status_code != 200:
        return []
    return r.json()
