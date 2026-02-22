# Catalog API — TODO (persistent)

This file is a human- and machine-readable TODO manifest for the Catalog API.
It's intended as the single source of truth for frontend AI logic (see `geminiservice.ts`) to display and track enrichment needs.

Format (JSON lines inside the fenced block) — the frontend may parse the JSON array to render tasks:

```json
[
  {
    "id": 1,
    "title": "Example dataset metadata missing schema",
    "description": "Fetch field schema for dataset '57f5fc9...' from ArcGIS and persist.",
    "status": "open",            /* open | in-progress | blocked | done */
    "priority": "high",         /* low | medium | high */
    "enrichment_needed": true,
    "assignee": null,
    "created_at": "2026-02-10T00:00:00Z",
    "updated_at": null,
    "notes": "Placeholder: geminiservice.ts will surface this to the UI and call ingestion endpoints."
  }
]
```

Usage
- Update this file by committing changes (CI may validate structure) or via the Catalog API's admin endpoints.
- `geminiservice.ts` should read and write this file (or a JSON equivalent endpoint) to keep the web front-end in sync.

Guidelines
- Keep entries small and actionable.
- Use `enrichment_needed: true` to indicate work for the enrichment pipeline.
- Use ISO 8601 timestamps for `created_at` and `updated_at`.

Notes
- This is intentionally minimal; a future work item is to implement an API-backed storage and locking mechanism so multiple actors can claim/complete tasks safely.

---

Gemini integration reference
---------------------------
The repository contains a `GeminiService` implementation at `azuredev-f777/geminiService.ts`. Key bindings and recommended usage:

- Env var: `API_KEY` — used by `GeminiService` to authenticate with Google GenAI.
- Exported instance: `gemini` (default instance of `GeminiService`).
- Methods:
  - `analyzeWithPro(prompt: string, base64Image?: string): Promise<string>` — multimodal analysis using `gemini-3-pro-preview`.
  - `fastResponse(prompt: string): Promise<string>` — low-latency text responses using `gemini-2.5-flash-lite-latest`.
  - `generateCode(userPrompt: string, dataframes: Array<{name,shape,columns}>): Promise<string>` — generate executable Python code for in-browser Pyodide notebooks.

Frontend note: `geminiservice.ts` should read/write this `TODO.md` (or a JSON-backed API) to claim and update enrichment tasks. See `catalog_api/gemini_integration.md` for a compact mapping to implementers.
