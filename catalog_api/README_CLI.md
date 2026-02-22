Catalog API CLI

Usage:

Run the CLI module with Python:

```bash
python -m catalog_api.cli enumerate-manifest --slug <manifest-slug> [--dry-run]
python -m catalog_api.cli sample-csv --csv path/to/file.csv --n 5
```

Commands:
- enumerate-manifest: locate a manifest in `catalog_api/sources/` by slug or `api_slug` and ingest its CSV-backed sources. Use `--dry-run` to only sample rows.
- sample-csv: sample and display inferred source rows from a CSV without touching the DB.

Notes:
- The CLI performs lazy imports and will not require a running database or SQLAlchemy for `--dry-run` or `--help`.
- For real ingestion runs, ensure dependencies in `requirements.txt` are installed and the env vars in `.env.template` are set.
