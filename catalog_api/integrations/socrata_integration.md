# Socrata integration


Use `catalog_api/fetchers/socrata_fetcher.py` to fetch view metadata (`/api/views/{id}.json`) and data preview (`/resource/{id}.json`).

Table of contents
- Overview
- Gemini roles
- Operational notes
- API tag / slug (placeholder)

Gemini roles
- `gemini.fastResponse` for concise dataset summaries and to suggest enrichment tasks.
- `gemini.analyzeWithPro` for deeper interpretation of column semantics or to reconcile conflicting metadata.
- `gemini.generateCode` to generate Pandas code to normalize Socrata previews for ingestion.

Operational notes
- Provide `SOCRATA_APP_TOKEN` via environment to increase rate limits.
- Manifests in `catalog_api/sources/` should list Socrata dataset ids (1:1 mapping to CSV rows where present).

API tag / slug (placeholder)
- `api_slug`: "socrata"
