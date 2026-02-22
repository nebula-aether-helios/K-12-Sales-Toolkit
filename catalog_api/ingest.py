import csv
import os
import time
from typing import Generator, Tuple, Dict, Any, Optional

from .config import settings
from . import storage
from .fetchers import socrata_fetcher, ckan_fetcher, arcgis_fetcher, github_fetcher
from .utils import safe_json_dumps


def seed_from_csv(csv_path: str) -> Generator[Tuple[str, str], None, None]:
    """Yield (source, source_id_or_url) for each row in csv.

    Heuristic: if a column named 'id' or 'dataset_id' exists, use it as source_id; if 'url' exists, yield as URL.
    """
    if not os.path.exists(csv_path):
        return
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get('url') or row.get('URL') or row.get('link')
            dsid = row.get('id') or row.get('dataset_id') or row.get('dataset')
            if url:
                # try to infer source
                low = url.lower()
                if 'socrata' in low or 'data.lacity.org' in low:
                    # extract id heuristic (last path segment)
                    parts = url.rstrip('/').split('/')
                    sid = parts[-1]
                    yield ('socrata', sid)
                elif 'arcgis' in low or 'featureserver' in low or 'services' in low:
                    # treat as arcgis service URL
                    yield ('arcgis', url)
                else:
                    yield ('url', url)
            elif dsid:
                yield ('unknown', dsid)


def ingest_dataset(source: str, source_id: str, site_base: Optional[str] = None):
    site_base = site_base or (settings.SOCRATA_SITES[0] if source == 'socrata' else None)
    metadata = {}
    preview = []
    if source == 'socrata' and site_base:
        metadata = socrata_fetcher.fetch_metadata(site_base, source_id)
        preview = socrata_fetcher.fetch_preview(site_base, source_id, n=25)
    elif source == 'ckan' and site_base:
        metadata = ckan_fetcher.fetch_metadata(site_base, source_id)
        preview = ckan_fetcher.fetch_preview(site_base, source_id, n=25)
    elif source == 'arcgis':
        # source_id is expected to be a service URL (may include layer)
        service_url = source_id
        metadata = arcgis_fetcher.fetch_metadata(service_url)
        preview = arcgis_fetcher.fetch_preview(service_url, n=25)
    else:
        metadata = {'title': None, 'description': None, 'raw': {}}
        preview = []

    dataset_id = storage.upsert_dataset(source, source_id, {**metadata, 'raw': metadata.get('raw', {}), 'schema': metadata.get('schema', {})})
    if preview:
        storage.save_preview(dataset_id, preview)
    time.sleep(settings.INGEST_SLEEP_SECONDS)
    return dataset_id


def ingest_sources_from_csv(csv_path: str, site_base: Optional[str] = None):
    for source, sid in seed_from_csv(csv_path):
        try:
            ingest_dataset(source, sid, site_base=site_base)
        except Exception as e:
            print(f"Failed to ingest {source}:{sid} — {e}")


def ingest_sources_from_manifest_slug(manifest_slug: str):
    """Load a manifest from catalog_api/sources/{manifest_slug}.json and ingest its CSV or repo sources.

    Supports manifests that include `source_csv` for CSV-backed sources.
    """
    import json
    from pathlib import Path

    sources_dir = Path(__file__).resolve().parent / 'sources'
    manifest_path = sources_dir / f"{manifest_slug}.json"
    if not manifest_path.exists():
        # try to find by api_slug inside files
        for p in sources_dir.glob('*.json'):
            try:
                j = json.loads(p.read_text(encoding='utf-8'))
                if j.get('api_slug') == manifest_slug:
                    manifest_path = p
                    break
            except Exception:
                continue
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest for {manifest_slug} not found")
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    mtype = manifest.get('type') or ''

    def _ingest_remote_file(url: str, title: str = None):
        """Download a remote CSV/JSON and store as a dataset preview."""
        import httpx
        try:
            r = httpx.get(url, timeout=30.0)
            if r.status_code != 200:
                print(f"Failed to download {url}: {r.status_code}")
                return None
            # simple CSV handling
            if url.lower().endswith('.csv') or 'text/csv' in (r.headers.get('content-type') or ''):
                text = r.text.splitlines()
                if not text:
                    return None
                reader = csv.reader(text)
                rows = list(reader)
                headers = rows[0] if rows else []
                preview_rows = []
                for row in rows[1:1+25]:
                    d = {headers[i] if i < len(headers) else f'col{i}': (row[i] if i < len(row) else None) for i in range(len(headers))}
                    preview_rows.append(d)
                meta = {'title': title or url.split('/')[-1], 'description': manifest.get('note'), 'schema': [{'name': h} for h in headers], 'source_url': url, 'raw': {}}
                dsid = storage.upsert_dataset('github', url, {**meta, 'raw': meta.get('raw', {}), 'schema': meta.get('schema', {})})
                if preview_rows:
                    storage.save_preview(dsid, preview_rows)
                return dsid
            else:
                # try json
                try:
                    j = r.json()
                    dsid = storage.upsert_dataset('github', url, {'title': title or url.split('/')[-1], 'description': manifest.get('note'), 'schema': {}, 'raw': j})
                    # save first element(s) as preview if list
                    if isinstance(j, list):
                        storage.save_preview(dsid, j[:25])
                    return dsid
                except Exception:
                    return None
        except Exception as e:
            print(f"Error fetching remote file {url}: {e}")
            return None

    # handle type-specific ingestion
    if mtype == 'csv':
        csv_rel = manifest.get('source_csv')
        if csv_rel:
            repo_root = Path(__file__).resolve().parent.parent
            csv_path = (repo_root / csv_rel).resolve()
            if csv_path.exists():
                # ingest the CSV file itself as a dataset
                with open(csv_path, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                    headers = rows[0] if rows else []
                    preview_rows = []
                    for row in rows[1:1+25]:
                        d = {headers[i] if i < len(headers) else f'col{i}': (row[i] if i < len(row) else None) for i in range(len(headers))}
                        preview_rows.append(d)
                meta = {'title': manifest.get('name') or manifest_slug, 'description': manifest.get('note'), 'schema': [{'name': h} for h in headers], 'source_url': str(csv_path)}
                dsid = storage.upsert_dataset('csv', str(csv_path), {**meta, 'raw': {}})
                if preview_rows:
                    storage.save_preview(dsid, preview_rows)
                return True
        return False

    if mtype == 'github':
        # manifest may include 'repo' (org URL) or list of 'example_repos'
        repo_field = manifest.get('repo')
        repos = []
        if repo_field:
            # if repo_field is org URL, list org repos
            owner, repo = github_fetcher._owner_repo_from_url(repo_field)
            if owner and not repo:
                repos = github_fetcher.list_org_repos(repo_field)
            elif owner and repo:
                repos = [f"{owner}/{repo}"]
        if not repos:
            repos = [r for r in manifest.get('example_repos', [])]

        for rname in repos:
            try:
                entries = github_fetcher.list_repo_files(rname, '')
                for e in entries:
                    if e.get('type') != 'file':
                        continue
                    name = e.get('name','').lower()
                    if name.endswith('.csv') or name.endswith('.json') or name.endswith('.geojson'):
                        url = e.get('download_url') or github_fetcher.raw_url_from_content_entry(e)
                        if url:
                            _ingest_remote_file(url, title=e.get('name'))
            except Exception as ex:
                print(f"Failed to process repo {rname}: {ex}")
        return True

    # fallback: if manifest points to a CSV, ingest it
    csv_rel = manifest.get('source_csv')
    if csv_rel:
        repo_root = Path(__file__).resolve().parent.parent
        csv_path = (repo_root / csv_rel).resolve()
        if csv_path.exists():
            ingest_sources_from_csv(str(csv_path))
            return True

    return False
