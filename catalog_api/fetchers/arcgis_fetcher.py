"""ArcGIS Feature Service fetcher helpers.
"""
from typing import List, Dict, Any
import httpx
import os


def _ensure_json(url: str) -> str:
    # append ?f=json if not present
    if '?f=json' in url or url.endswith('?f=json'):
        return url
    if url.endswith('/'):
        return url + '?f=json'
    return url + '?f=json'


def _to_str_url(u):
    # coerce url-like inputs into a proper string URL
    try:
        if isinstance(u, tuple):
            # tuple like (b'scheme', b'host', None, b'/path')
            scheme = u[0].decode() if isinstance(u[0], bytes) else u[0]
            host = u[1].decode() if isinstance(u[1], bytes) else u[1]
            path = u[3].decode() if isinstance(u[3], bytes) else (u[3] or '')
            return f"{scheme}://{host}{path}"
        return str(u)
    except Exception:
        return str(u)


def fetch_metadata(service_url: str, layer: str = '') -> Dict[str, Any]:
    """Fetch ArcGIS service/layer metadata. `service_url` may be a service or a layer URL.

    If `layer` is provided it will be appended as '/{layer}'.
    """
    base = service_url.rstrip('/')
    if layer:
        base = f"{base}/{layer}"
    base = _to_str_url(base)
    url = _ensure_json(base)
    headers = {}
    token = os.getenv('ARCGIS_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    try:
        r = httpx.get(_to_str_url(url), timeout=20.0, headers=headers)
        if r.status_code != 200:
            return {'title': None, 'description': None, 'raw': {'error': r.text}}
        j = r.json()
        # If this is a layer response it will contain 'fields'. If it's a service, inspect layers and fetch first layer metadata.
        fields = j.get('fields') or []
        if not fields:
            layers = j.get('layers') or []
            if layers:
                first_layer = layers[0]
                lid = first_layer.get('id')
                layer_url = base.rstrip('/') + f'/{lid}?f=json'
                try:
                    rr = httpx.get(_to_str_url(layer_url), timeout=20.0, headers=headers)
                    if rr.status_code == 200:
                        lj = rr.json()
                        fields = lj.get('fields') or []
                        title = lj.get('name') or lj.get('layerName')
                        desc = lj.get('description') or ''
                        schema = [{'name': f.get('name'), 'type': f.get('type'), 'alias': f.get('alias')} for f in fields]
                        return {'title': title, 'description': desc, 'schema': schema, 'source_url': layer_url, 'raw': lj}
                except Exception:
                    pass
        title = j.get('name') or j.get('serviceName')
        desc = j.get('description') or j.get('serviceDescription')
        schema = [{'name': f.get('name'), 'type': f.get('type'), 'alias': f.get('alias')} for f in fields]
        return {'title': title, 'description': desc, 'schema': schema, 'source_url': base, 'raw': j}
    except Exception as e:
        return {'title': None, 'description': None, 'raw': {'error': str(e)}}


def fetch_preview(service_url: str, layer: str = '', n: int = 10) -> List[Dict[str, Any]]:
    """Query the ArcGIS feature service for up to `n` rows."""
    base = service_url.rstrip('/')
    if layer:
        base = f"{base}/{layer}"
    # if base points to a service (no '/0'), try to discover first layer
    query_base = base
    if not base.rstrip('/').endswith('/query'):
        # if base looks like a FeatureServer service (no layer), fetch service json to find first layer
        if base.rstrip('/').endswith('/FeatureServer'):
            try:
                svc = httpx.get(_to_str_url(_ensure_json(base)), timeout=10.0)
                if svc.status_code == 200:
                    sj = svc.json()
                    layers = sj.get('layers') or []
                    if layers:
                        lid = layers[0].get('id')
                        query_base = base + f'/{lid}'
            except Exception:
                pass
        query_url = query_base + ('/query' if not query_base.endswith('/query') else '')
    params = {
        'where': '1=1',
        'outFields': '*',
        'resultRecordCount': n,
        'f': 'json'
    }
    headers = {}
    token = os.getenv('ARCGIS_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    try:
        r = httpx.get(_to_str_url(query_url), params=params, timeout=20.0, headers=headers)
        if r.status_code != 200:
            return []
        j = r.json()
        features = j.get('features') or []
        rows = [f.get('attributes', {}) for f in features]
        return rows
    except Exception:
        return []
