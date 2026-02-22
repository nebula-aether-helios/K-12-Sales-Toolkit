Archive proposal (review before any move/delete)

These are candidate files and patterns I propose we move to `ARCHIVE/` to eliminate duplication and conflicting legacy processes.

Candidate files / patterns:

- `v2.txt` (large legacy notes / duplicates)
- `v3mvp-1.ipynb`, `EnrichmentPipeline.ipynb`, other legacy notebooks that are not actively used in CI
- `Untitled-1.md`, `runforme_mvp_control_center v1.txt`, `v3_use_case_doc_locked.txt` (old notes / locked docs — keep a copy but move to archive folder)
- `planB/`, `Realignment/` (if Realignment content already merged into `v3_realignment_config.py`, consider archiving duplicates; retain `v3_realignment_config.py` in active set)
- Any `*.txt` or `*.md` files that are brainstorming or drafts and not referenced by active code (I'll list exact files if you want me to auto-move)
- Old ad-hoc scripts that duplicate `scripts/` functionality — e.g., `scripts/*_old.py`, `batch_debug_errors.py` if duplicates exist

Proposed safe steps (I will wait for your approval):
1. Create `ARCHIVE/` directory at repo root.
2. Move listed candidate files into `ARCHIVE/` (preserving them exactly).
3. Add `ARCHIVE/README.md` with a short explanation and timestamped manifest of moved files.
4. Optionally commit the changes on a cleanup branch (recommended) instead of directly on main.

If you approve, I will: create `ARCHIVE/`, move the listed candidates (or the exact files you confirm), and add the manifest. If you prefer, I can instead produce a git-branch patch you can review and merge.
