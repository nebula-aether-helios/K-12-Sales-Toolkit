# CKAN integration


Use `catalog_api/fetchers/ckan_fetcher.py` to call CKAN `package_show` and retrieve resource URLs for previews. If resources are CSV/JSON, download and parse for schema and preview rows.

Table of contents
- Overview
- Gemini roles
- Operational notes
- API tag / slug (placeholder)

Gemini roles
- Use `gemini.fastResponse` for short metadata summaries.
- Use `gemini.analyzeWithPro` to infer schema from partial previews when resources have inconsistent formatting.
- Use `gemini.generateCode` to create Pyodide snippets for CSV cleaning.

Operational notes
- CKAN instances vary; prefer explicit resource URLs from `package_show` rather than relying on `result.url`.
- Update manifests in `catalog_api/sources/` for any CKAN endpoints discovered.

API tag / slug (placeholder)
- `api_slug`: "ckan"
