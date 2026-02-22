from fastapi import FastAPI, HTTPException, BackgroundTasks
from typing import Optional

from . import storage
from .models import DatasetOut, PreviewOut
from .ingest import ingest_dataset
from .ingest import ingest_sources_from_manifest_slug
import json
from pathlib import Path


_SOURCES_DIR = Path(__file__).resolve().parent / 'sources'


def _load_manifests() -> dict:
    manifests = {}
    if not _SOURCES_DIR.exists():
        return manifests
    for p in _SOURCES_DIR.glob('*.json'):
        try:
            j = json.loads(p.read_text(encoding='utf-8'))
            slug = j.get('api_slug') or j.get('name') or p.stem
            manifests[slug] = j
        except Exception:
            continue
    return manifests

app = FastAPI(title="Catalog API", version="0.1")


@app.on_event('startup')
def on_startup():
    storage.init_db()


@app.get('/health')
def health():
    return {"status": "ok"}


@app.get('/datasets')
def list_datasets(limit: int = 50, offset: int = 0, q: Optional[str] = None, source: Optional[str] = None):
    results = storage.get_datasets(limit=limit, offset=offset, q=q, source=source)
    return results


@app.get('/datasets/{dataset_id}')
def get_dataset(dataset_id: int):
    ds = storage.get_dataset_by_id(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail='Dataset not found')
    return ds


@app.get('/datasets/{dataset_id}/preview')
def get_preview(dataset_id: int, n: int = 10):
    rows = storage.get_preview(dataset_id, n=n)
    return {"dataset_id": dataset_id, "rows": rows}


@app.post('/ingest')
def post_ingest(background_tasks: BackgroundTasks, source: str, source_id: str, site_base: Optional[str] = None):
    # schedule ingestion in background
    background_tasks.add_task(ingest_dataset, source, source_id, site_base)
    return {"status": "accepted", "source": source, "source_id": source_id}


@app.get('/sources')
def list_sources():
    """Return available source manifests keyed by api_slug."""
    return _load_manifests()


@app.get('/sources/{slug}')
def get_source(slug: str):
    manifests = _load_manifests()
    m = manifests.get(slug)
    if not m:
        raise HTTPException(status_code=404, detail='Source manifest not found')
    return m


@app.post('/sources/{slug}/enumerate')
def post_enumerate_source(slug: str, background_tasks: BackgroundTasks):
    """Trigger ingestion/enumeration for the given manifest slug. Runs in background."""
    # schedule background ingestion from manifest
    background_tasks.add_task(ingest_sources_from_manifest_slug, slug)
    return {"status": "accepted", "slug": slug}
