# OSHA GitHub integration


Treat the OSHA GitHub org as a collection of dataset repositories. Use the GitHub API to list repositories and raw file contents; process CSV/JSON files found in repos as dataset seeds.

Table of contents
- Overview
- Gemini roles
- Operational notes
- API tag / slug (placeholder)

Gemini roles
- `gemini.fastResponse` to summarize repository README and dataset descriptions.
- `gemini.analyzeWithPro` to interpret complex JSON/CSV schemas and map fields to the Catalog schema.
- `gemini.generateCode` to create Pyodide data loading snippets for previewing repo-hosted datasets.

Operational notes
- Use authenticated GitHub API requests when possible to avoid low rate limits.
- Only fetch raw files of a limited size for previews; for large files, fetch a head sample or use the repo's releases/archives.
- Record 1:1 mapping between each discovered dataset file and a Catalog dataset entry in `catalog_api/sources/` manifests.

API tag / slug (placeholder)
- `api_slug`: "github:oshadata"
