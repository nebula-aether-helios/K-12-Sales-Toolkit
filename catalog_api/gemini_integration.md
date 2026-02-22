Public methods and recommended usage
- `analyzeWithPro(prompt: string, base64Image?: string): Promise<string>`
  - Use for: deep reasoning tasks and image + text analysis (e.g., analyze dataset preview image, infer schema from screenshots).
  - Input: natural-language prompt and optional base64-encoded image.
  - Output: plain text analysis string; errors are returned as string starting with `Error:`.

Table of contents
- Overview
- Public methods
- Frontend usage notes
- Integration patterns
- API tag / slug (placeholder)

Frontend usage notes (for `geminiservice.ts` integration):
# Gemini integration mapping (catalog_api)

This document maps `geminiService.ts` methods to the Catalog API front-end responsibilities. It's intended to help implementers wire the AI frontend to backend task management.

File: `azuredev-f777/geminiService.ts`

Exported instance:
- `gemini` — instance of `GeminiService`

Public methods and recommended usage
- `analyzeWithPro(prompt: string, base64Image?: string): Promise<string>`
  - Use for: deep reasoning tasks and image + text analysis (e.g., analyze dataset preview image, infer schema from screenshots).
  - Input: natural-language prompt and optional base64-encoded image.
  - Output: plain text analysis string; errors are returned as string starting with `Error:`.

- `fastResponse(prompt: string): Promise<string>`
  - Use for: short summaries, confirmations, and quick NL responses (e.g., summarize dataset metadata, confirm task assignment).
  - Input: prompt string. Output: text string.

- `generateCode(userPrompt: string, dataframes: Array<{name,shape,columns}>): Promise<string>`
  - Use for: generating executable Python snippets for in-browser Pyodide notebooks. Pass current DataFrame context as `dataframes`.
  - Output: raw Python code (the service strips code fences when possible).

Auth & Environment
- `API_KEY` environment variable — must be present for the service to function.

Integration patterns for `catalog_api`
- Task surfacing: the front-end may read `catalog_api/TODO.md` (JSON block) and present tasks; when claiming/updating, the front-end should call a backend admin endpoint (future) or update the file and commit.
- Suggested bindings:
  - UI 'Summarize' action -> call `gemini.fastResponse` with a concise prompt (include dataset title + sample rows).
  - UI 'Analyze' action -> call `gemini.analyzeWithPro` with prompt + optional screenshot/base64 preview.
  - UI 'Generate code' action -> call `gemini.generateCode` with user request + DataFrame context.

Security & rate-limits
- Keep `API_KEY` server-side; do not expose to browsers. Proxy Gemini calls through a server endpoint with rate-limiting and token usage accounting.

Notes for implementers
- `gemini.generateCode` enforces rules in its system prompt: it returns only executable Python code. The UI should display raw code and offer a single-click run in the Pyodide context.
- The front-end should treat any response beginning with `Error:` as a soft failure and surface the message to the operator.
