# California Department of Consumer Affairs (DCA) integration


Sources
- DCA exposes multiple license lookup portals and datasets (contractors, boards, professional licensing). Prefer official CSV/JSON exports or lookup APIs.

Table of contents
- Overview
- Integration pattern
- Gemini roles
- Operational notes
- API tag / slug (placeholder)

Integration pattern
- For CSV seeds (e.g., CSLB exports), use the existing CSV seeder to create one-to-one catalog entries.
- For lookup APIs, implement small adapters to query by license number and retrieve structured metadata.

Gemini roles
- `gemini.fastResponse` for summarizing licensing statuses.
- `gemini.analyzeWithPro` to reconcile inconsistent fields across multiple DCA boards.
- `gemini.generateCode` to produce Pyodide data-cleaning snippets for irregular CSV formats.

Operational notes
- Some DCA pages are interactive; prefer official open data endpoints where available. Respect scraping policies and robots.txt when falling back to web scraping.

API tag / slug (placeholder)
- `api_slug`: "dca"
