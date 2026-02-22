Table of contents
- Overview
- Integration pattern
- Gemini roles
- Operational notes
- API tag / slug (placeholder)

# California / LA Accessors integration

Scope
- Public portals such as LA County GIS, statewide `data.ca.gov`, and LA vote/administration portals.

Integration pattern
- Discover CSV/JSON files through manifests or portal search pages; add each discovered file as a 1:1 dataset entry in the Catalog.
- Use `arcgis_fetcher` for ArcGIS-hosted layers; use `socrata_fetcher` for Socrata portals.

Gemini roles
- `gemini.fastResponse` to produce short human-friendly descriptions of portal datasets.
- `gemini.analyzeWithPro` to infer schema from mixed-format dataset previews.
- `gemini.generateCode` to generate cleaning/transformation snippets.

Operational notes
- Maintain a manifest entry per discovered dataset file/endpoint under `catalog_api/sources/` to preserve 1:1 mapping.
