Active files (primary working set)

These are the files and directories I propose we treat as "active" and keep prominent at the repo root.

- `.env` (main environment file — single source of truth)
- `requirements.txt`
- `README.md`
- `INSTRUCTIONS.md`
- `scripts/` (smoke tests, batch helpers)
  - `scripts/smoke_enrich_batch.py`
  - `scripts/smoke_enrich_errors.py`
  - `scripts/find_problematic_rows.py`
  - any other scripts that are part of the enrichment QA flow
- `ferengi_full_enrichment.py` (primary full-run enricher)
- `deep_enrichment_pipeline.py` (async pipeline + trigger logic)
- `v3_enhanced_enrichment.py` (enrichment modules — DNS / GP / OSHA / Permits / Craiglist)
- `run_ferengi_all.py` (controller / orchestrator)
- `scripts/full_db_enrich.py` (CLI entrypoint / dashboard)
- `run_ferengi_all.py` (runner)
- `outputs/` (kept but not tracked for source-of-truth; contains export artifacts)
- `catalog_api/` (API ingest and CLI helpers)
- `connectors/` (integration adapters)
- `src/`, `tests/` (if present)

Notes:
- I haven't changed any files yet. This file is a proposed active set; please review.
- Next step (after your confirmation): either move older/conflicting files into `ARCHIVE/` or create a git-branch that performs the archival.
