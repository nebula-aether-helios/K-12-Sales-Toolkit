# Catalog API

Small FastAPI service to register and preview public datasets (Socrata/CKAN/CSV seed).

Run locally:

1. Create `.env` from `.env.template` and edit if needed.
2. Initialize DB:

```bash
python -m catalog_api.runner --init-db
```

3. Seed from a CSV (example uses `City of Los Angeles Geohub.csv`):

```bash
python -m catalog_api.runner --seed-csv "City of Los Angeles Geohub.csv"
```

4. Start the API:

```bash
uvicorn catalog_api.main:app --reload
```

Endpoints:
- GET /datasets
- GET /datasets/{id}
- GET /datasets/{id}/preview
- POST /ingest?source=&source_id=&site_base=

Notes:
- This is an initial scaffold. Socrata/CKAN fetchers are minimal and may need expansion for production.
- Respect public API rate limits and set `SOCRATA_APP_TOKEN` in `.env` for higher quotas.
