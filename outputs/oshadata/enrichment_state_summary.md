# OSHA Enrichment — Critical State Summary

Date: 2026-02-11

Purpose
- Working locally only (no git commits) to enrich the Sacramento CSLB contractor seed using OSHA DataDoor datasets.

What I ran and produced
- Fetched OSHA datasets from GitHub into: `outputs/oshadata/OSHADataDoor_OshaScrapy/`:
  - `accidents_asof_022315.csv` (incident-level)
  - `RIDlookup.csv` (RID -> state lookup)
  - `state_employment.csv`
- Created local manifest JSONs (for bookkeeping only) under `catalog_api/sources/`:
  - `oshadata_accidents.json`
  - `oshadata_ridlookup.json`
  - `oshadata_state_employment.json`
- Implemented and ran `scripts/osha_local_enrich.py` (smoke test):
  - Input: `outputs/oshadata/OSHADataDoor_OshaScrapy/accidents_asof_022315.csv`
  - Output: `outputs/oshadata/OSHADataDoor_OshaScrapy/accidents_asof_022315_enriched.csv`
  - Stats (full run): rows processed: 105,483; fatality rows: 48,729
  - Initial exact mapping had many misses; improved mapping applied with digit-normalization, prefix heuristics and `rapidfuzz` fuzzy RID matching to reach 0 missing state mappings.
  - `outputs/oshadata/OSHADataDoor_OshaScrapy/unmatched_sample.csv` written (up to 200 rows) for inspection (empty after fuzzy pass).

- Implemented contractor matching pipelines (local, no external APIs):
  - `scripts/osha_contractor_tfidf_enrich.py` — TF-IDF + `rapidfuzz` preview matching (preferred, lightweight).
  - `scripts/osha_contractor_bert_enrich.py` — sentence-transformers approach added but not required (heavy installs).
  - Ran TF-IDF preview (100 rows): `outputs/sacramento_contractors_cslb_sac_enriched_preview_tfidf.csv`

Environment & deps
- Updated `requirements.txt` locally (for reproducibility) to include `rapidfuzz` and `sentence-transformers` (sentence-transformers not required for TF-IDF flow).
- Installed `rapidfuzz` in the environment; `sentence-transformers` installation was attempted but is heavy and not needed for current TF-IDF flow.

Decisions & notes
- No git commits will be made — this is a local enrichment workflow only.
- Preferred local approach: TF-IDF (scikit-learn) + `rapidfuzz` token-set refinement. This gives strong semantic matching without heavy transformer installs.

Next actionable options (pick one):
1. Tune thresholds and weights (TF-IDF vs rapidfuzz).
  - Recommended combined formula (balanced): 0.7 * TFIDF + 0.3 * (rapidfuzz/100). Default threshold = 0.50.
  - Stricter mode (higher precision): 0.8 * TFIDF + 0.2 * (rapidfuzz/100). Default threshold = 0.55.
  - Safer mode (favor recall / more matches): 0.6 * TFIDF + 0.4 * (rapidfuzz/100). Default threshold = 0.45. (previous default)
  - Calibration note: run the TF-IDF preview over a representative labeled sample (e.g., 500–2,000 rows), then pick the threshold/weight that balances precision/recall for your use case. A recommended starting flow: try balanced (0.7/0.3, 0.50), inspect false positives/negatives, then switch to stricter if precision is more important.
2. Expand preview to full dataset and perform a persistent join to update contractor rows with: `osha_inspection_count`, `osha_last_inspection_date`, `osha_penalty_total` (best-effort aggregation).
3. Add rules to only propagate matches with extra safety checks (same state, similarity > 0.6, and exact report_id match if present).

Quick commands (local)
```bash
# TF-IDF preview (100 rows)
python scripts/osha_contractor_tfidf_enrich.py --preview 100

# Expand to full dataset (example - will run longer)
python scripts/osha_contractor_tfidf_enrich.py --preview 9741
```

Files of interest (local)
- Seed: `outputs/sacramento_contractors_cslb_sac.csv`
- OSHA raw: `outputs/oshadata/OSHADataDoor_OshaScrapy/accidents_asof_022315.csv`
- OSHA enriched: `outputs/oshadata/OSHADataDoor_OshaScrapy/accidents_asof_022315_enriched.csv`
- Contractor preview: `outputs/sacramento_contractors_cslb_sac_enriched_preview_tfidf.csv`

Status
- All enrichment work was executed locally. No commits performed.

If you want me to proceed, tell me which of the three "Next actionable options" to run and I will do it locally and save results to `outputs/`.
