# ArcGIS integration (City/County GeoHub)


Use `catalog_api/fetchers/arcgis_fetcher.py` to retrieve metadata and small previews from FeatureServer endpoints listed in the CSV manifests.

Table of contents
- Overview
- Gemini roles
- Operational notes
- API tag / slug (placeholder)

Gemini roles
- For quick summaries: call `gemini.fastResponse` with dataset title + short description.
- For schema inference: call `gemini.analyzeWithPro` with a prompt containing a sample of field names and several sample rows.
- For code generation to transform previews: call `gemini.generateCode` with DataFrame context.

Operational notes
- Prefer the FeatureServer `/query?f=json` endpoint for previews. Respect `INGEST_PAGE_SIZE` when paginating.
- Map CSV rows to dataset entries 1:1 via the `catalog_api/sources/*.json` manifests.

API tag / slug (placeholder)
- `api_slug`: "arcgis"  # replace or refine with actual endpoint/route when available
