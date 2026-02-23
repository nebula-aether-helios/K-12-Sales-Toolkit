# Stage 3 Executive Review — Dev Team Audit Package

> **Author:** Stage 3 Automation (Cursor Agent)
> **Date:** 2026-02-22
> **Purpose:** Comprehensive pre-push review for development team audit, testing, and feedback
> **Criticality:** HIGH — This deliverable is for a career-defining job application

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [What Was Done (Stage 3 Changes)](#2-what-was-done)
3. [Critical Issues Found & Fixed](#3-critical-issues-found--fixed)
4. [Known Issues — Remaining (Not Fixed)](#4-known-issues--remaining)
5. [Dependency Audit — Complete](#5-dependency-audit--complete)
6. [File-by-File Review Status](#6-file-by-file-review-status)
7. [Notebook Validity](#7-notebook-validity)
8. [Testing & CI Status](#8-testing--ci-status)
9. [Streamlit Cloud Deployment Readiness](#9-streamlit-cloud-deployment-readiness)
10. [README & Documentation Gaps](#10-readme--documentation-gaps)
11. [Action Items for Dev Team](#11-action-items-for-dev-team)
12. [Zip Package Contents](#12-zip-package-contents)

---

## 1. Executive Summary

The K-12 Sales Intelligence Toolkit underwent a three-stage development process:

- **Stage 1 (Jules/Gemini):** Initial scaffold — notebooks, Streamlit app, data pipelines, tests
- **Stage 2 (Gemini handoff):** Review report, additional features, refinements
- **Stage 3 (Cursor Agent):** Comprehensive audit, correctness fixes, deep work additions, and this review

### Stage 3 delivered 5 correctness fixes and 4 new features:

| Category | Item | Status |
|----------|------|--------|
| Fix | CSV path fallback (2025→2024) in 2 notebooks | DONE |
| Fix | `sys.path` resolution in all 9 notebooks | DONE (see caveat in §4) |
| Fix | `run_data_collection.py` missing `fetch_cde_admin_directory` | DONE |
| Fix | README tech stack accuracy (removed false XGBoost claims) | DONE |
| Fix | `STAGE2_REVIEW_REPORT.md` complete rewrite | DONE |
| Feature | CLV model (`src/clv_model.py`) — BG/NBD + Gamma-Gamma | DONE |
| Feature | HubSpot CRM integration in pipeline tracker | DONE |
| Feature | Streamlit Cloud deployment config | DONE |
| Feature | Loom walkthrough script (`docs/WALKTHROUGH_SCRIPT.md`) | DONE |

### Post-delivery audit found and fixed 7 additional issues:

| Severity | ID | Issue | Fix Applied |
|----------|----|-------|-------------|
| **CRITICAL** | C1 | `clv_model.py`: `summary_data_from_transaction_data` called before availability guard | YES — added fallback RFM calculation |
| **CRITICAL** | C2 | `clv_model.py`: `.rename(columns={"index": "district_name"})` was a no-op | YES — dynamic column detection |
| **CRITICAL** | C4/C5 | `streamlit_app.py`: `exec()` + `os.chdir()` — security, tracing, race condition | YES — replaced with `importlib.util` |
| **CRITICAL** | C3 | `04_pipeline_tracker.py`: unguarded `dotenv` import crashes if missing | YES — try/except |
| **MODERATE** | M4 | `04_pipeline_tracker.py`: tz-aware/naive datetime mixing with HubSpot | YES — UTC normalization |
| **MODERATE** | M6 | `04_pipeline_tracker.py`: division by zero on empty pipeline | YES — guard |
| **HIGH** | X1 | `lifetimes` missing from Streamlit demo `requirements.txt` | YES — added |

---

## 2. What Was Done

### 2.1 Correctness Fix — CSV Paths

**Files:** `01_district_intelligence/california_district_prioritization_model.ipynb`, `01_district_intelligence/la_unified_opportunity_analysis.ipynb`

Both notebooks previously loaded `caaspp_ela_2024.csv`. Changed to try `caaspp_ela_2025.csv` first (5,387 rows of real 2025 CAASPP data now exist in `data/processed/`) with `try/except FileNotFoundError` fallback to 2024.

### 2.2 Correctness Fix — sys.path

**Files:** All 9 `.ipynb` files

Changed from `os.path.join(os.getcwd(), "src")` to:
```python
_nb_dir = os.path.dirname(os.path.abspath('__file__'))
_repo_root = os.path.abspath(os.path.join(_nb_dir, '..'))
sys.path.insert(0, os.path.join(_repo_root, 'src'))
```

**CAVEAT (see §4):** `'__file__'` is a string literal, not the `__file__` variable. In Jupyter, `os.path.abspath('__file__')` resolves against CWD, making `_nb_dir == os.getcwd()`. This works because Jupyter defaults CWD to the notebook's directory. The fix is functionally equivalent to the original but more verbose. It is **not** truly portable to arbitrary CWDs as originally intended.

### 2.3 Correctness Fix — Data Collection

**File:** `data/run_data_collection.py`

Added `fetch_cde_admin_directory` import and call as step 5/5. All step labels updated.

### 2.4 Correctness Fix — README Tech Stack

**Files:** Both `README.md` files

Removed false claims of XGBoost, httpx, langchain. Accurately describes:
- RandomForestClassifier in notebooks
- Weighted linear formula in Streamlit
- Added CLV modeling row for `lifetimes`

### 2.5 Feature — CLV Model

**File:** `src/clv_model.py` (NEW)

Full BG/NBD + Gamma-Gamma implementation using the `lifetimes` library:
- Synthesizes transaction patterns from CAASPP proficiency gaps + ESSER funding
- Outputs 3-year CLV, churn probability, CLV tier per district
- Graceful fallback when `lifetimes` is not installed (manual RFM calculation)
- Integrated into `07_streamlit_demo/pages/01_district_prioritizer.py` as additional columns

### 2.6 Feature — HubSpot Integration

**File:** `07_streamlit_demo/pages/04_pipeline_tracker.py` (MODIFIED)

- `_load_hubspot_deals()`: Connects to HubSpot Deals API v3 when `HUBSPOT_API_KEY` env var is set
- Fallback to demo data with real LA-area district names
- Uses `requests` directly (not the `hubspot-api-client` SDK)
- UI connection status indicator

### 2.7 Feature — Streamlit Cloud Deploy

**Files:** `streamlit_app.py` (repo root, NEW), `.streamlit/config.toml` (NEW)

- `streamlit_app.py`: Thin entrypoint that imports the real `app.py` via `importlib.util`
- `config.toml`: Brand theme (LP orange #F7941D primary, deep blue #2E5A88 text)
- Deploy badge added to both READMEs

### 2.8 Feature — Walkthrough Script

**File:** `K-12-Sales-Toolkit/docs/WALKTHROUGH_SCRIPT.md` (NEW)

60-second Loom demo storyboard with script, screen directions, and recording tips.

---

## 3. Critical Issues Found & Fixed

### C1: `clv_model.py` — NameError when lifetimes not installed

**Before:** `summary_data_from_transaction_data()` was called on line 128 unconditionally. If `lifetimes` was not installed, this function (imported conditionally inside try/except) would raise `NameError`.

**After:** The `if not LIFETIMES_AVAILABLE` branch now comes first with a manual RFM aggregation using pandas `groupby`. The `summary_data_from_transaction_data` call is only reached in the `else` (lifetimes available) branch.

### C4/C5: `streamlit_app.py` — exec() + os.chdir()

**Before:**
```python
os.chdir(_DEMO)
exec(open(os.path.join(_DEMO, "app.py"), encoding="utf-8").read())
```

Problems:
1. `exec()` breaks `__file__` resolution in the exec'd code
2. `os.chdir()` mutates global process state (race condition on Cloud)
3. Resource leak (file handle never closed)
4. Stack traces show `<string>` instead of actual filename

**After:**
```python
spec = importlib.util.spec_from_file_location("app", os.path.join(_DEMO, "app.py"))
app_module = importlib.util.module_from_spec(spec)
app_module.__file__ = os.path.join(_DEMO, "app.py")
spec.loader.exec_module(app_module)
```

This preserves `__file__` resolution, avoids global state mutation, and produces proper tracebacks.

### C3: `04_pipeline_tracker.py` — dotenv crash

`from dotenv import load_dotenv` was unguarded. `python-dotenv` is listed in requirements but may not be installed in minimal environments. Wrapped in `try/except ImportError`.

### M4: Pipeline tracker timezone mixing

HubSpot API returns ISO 8601 timestamps with `Z` suffix (UTC). The code mixed `datetime.now()` (tz-naive) with `pd.to_datetime()` results (tz-aware), causing `TypeError` on subtraction. Fixed by parsing with `utc=True` and then stripping tz info to work with naive datetimes consistently.

### M6: Pipeline tracker division by zero

`weighted_pipeline / total_pipeline * 100` would crash if all deals had zero value. Added a ternary guard.

### X1: Missing lifetimes in Streamlit requirements

`lifetimes>=0.11.0` was added to the main `requirements.txt` but not to `07_streamlit_demo/requirements.txt`. Since `01_district_prioritizer.py` imports `compute_clv` which imports `lifetimes`, the CLV feature would silently fail on Streamlit Cloud. Fixed by adding it.

### Stale notebook outputs

`california_district_prioritization_model.ipynb` had 4 cells with cached outputs containing generic "District 62" names, all-zero feature importances (degenerate model from fallback data), and "Tier 1 targets: 0". All cleared to `execution_count: null` and `outputs: []`.

---

## 4. Known Issues — Remaining (Not Fixed)

These are documented for the dev team to assess. Sorted by severity.

### MODERATE SEVERITY

| ID | File | Issue | Impact | Recommendation |
|----|------|-------|--------|----------------|
| M3 | `clv_model.py:78` | ESSER fuzzy match uses `district.split(" ")[0]` — "El Monte" matches on just "El", creating false positives with "El Segundo" etc. | CLV values may be inflated for some districts | Use `fuzzywuzzy` ratio matching or exact substring |
| M7 | `01_district_prioritizer.py:60` | CLV merge on `district_name` — if CLV model's names don't exactly match dashboard names (whitespace, casing), merge silently produces NaN filled with defaults ($0 CLV, 0.5 churn) | Misleading CLV data shown to user | Add fuzzy matching or normalize both sides |
| M9 | `01_district_prioritizer.py:84` | Boolean filter uses bare Python `True` literal instead of boolean Series. Works via pandas broadcasting but is fragile. | Unlikely to crash but bad practice | Use `pd.Series(True, index=districts.index)` |
| M12 | `utils.py:268` | Case-sensitive column name check `if "grade" in caaspp.columns` — will miss `"Grade"` (capital G) from legacy CSV files | Data loading may skip district-level aggregation | Use `caaspp.columns.str.lower()` normalization |
| M15 | `utils.py:285` | FRPM aggregation uses `"first"` strategy for all columns — takes arbitrary school's data instead of summing enrollment/frpm_count at district level | Enrollment figures may be wrong (showing single school, not full district) | Use `"sum"` for numeric columns, `"first"` for categorical |
| M16 | `data_fetchers.py:65` | `open(cache_path, "rb").read()` without context manager — file handle leak | Minor memory leak on repeated calls | Use `with open() as f:` |
| M17 | `data_fetchers.py:20` | `from bs4 import BeautifulSoup` is a hard import — `beautifulsoup4` not in Streamlit demo requirements | Crash if `data_fetchers` is imported from Streamlit context | Add to Streamlit requirements or lazy-import |
| M18 | `data_fetchers.py:116` | Column name whitespace sensitivity with caret-delimited CAASPP files — no `.strip()` on headers | Silent data loss if headers have trailing spaces | Add `df.columns = df.columns.str.strip()` after read |

### LOW SEVERITY

| ID | File | Issue |
|----|------|-------|
| m2 | `src/` | No `__init__.py` — all imports rely on `sys.path` manipulation |
| m3 | `04_pipeline_tracker.py` | Inconsistent `stage_weights` data structure (dict vs list between two functions) |
| m4 | `04_pipeline_tracker.py` | `.dt.to_period("M")` may fail on tz-aware datetime in Plotly chart |
| m5 | `01_district_prioritizer.py` | `clv_tier` loses CategoricalDtype after merge + fillna |
| m6 | `run_data_collection.py:15` | Redundant CWD-dependent `sys.path.append` fallback |
| m10 | `data_fetchers.py:378` | `import re` inside function body (unconventional) |

### sys.path DESIGN NOTE

The `'__file__'` string-literal approach used across all 9 notebooks resolves to `os.getcwd()` in Jupyter (since `__file__` is not defined in notebooks and `os.path.abspath('__file__')` treats the literal string as a relative path). This works **only** because Jupyter/VS Code notebook kernels default CWD to the notebook's directory. If a user runs a notebook after `os.chdir()` to a different directory, imports will break.

**Dev team recommendation:** Either accept this limitation (it matches Jupyter conventions) or switch to an explicit `os.getcwd()` call to make the behavior transparent rather than accidental.

---

## 5. Dependency Audit — Complete

### 5.1 Actually Imported (26 packages)

| Package | Import Name | Used In |
|---------|-------------|---------|
| `pandas` | `pandas` | 23 files (all notebooks, all Streamlit pages, all src modules) |
| `numpy` | `numpy` | 14 files |
| `scikit-learn` | `sklearn` | 2 notebooks: `california_district_prioritization_model.ipynb`, `solving_teacher_buy_in_challenge.ipynb` |
| `matplotlib` | `matplotlib` | 9 files (8 notebooks + `visualization_theme.py`) |
| `seaborn` | `seaborn` | 4 notebooks |
| `plotly` | `plotly` | 6 files (2 notebooks + 3 Streamlit pages + `visualization_theme.py`) |
| `requests` | `requests` | 3 files (`la_unified_opportunity_analysis.ipynb`, `04_pipeline_tracker.py`, `data_fetchers.py`) |
| `beautifulsoup4` | `bs4` | 2 files (`la_unified_opportunity_analysis.ipynb`, `data_fetchers.py`) |
| `google-generativeai` | `google.generativeai` | 5 files (email generator, superintendent engine, discovery call, deal coach, researcher) |
| `streamlit` | `streamlit` | 8 files (all Streamlit pages + app + utils) |
| `python-dotenv` | `dotenv` | 7 files |
| `fpdf2` | `fpdf` | 1 file (`generate_territory_report.py`) |
| `lifetimes` | `lifetimes` | 1 file (`clv_model.py`) — **NEW in Stage 3** |
| `pytest` | `pytest` | 1 file (`test_district_scoring.py`) |

### 5.2 NOT Imported — Ghost Dependencies (19 packages)

| Package | Category | Provenance | Recommendation |
|---------|----------|------------|----------------|
| `scipy` | Core Data Science | Original scaffold | **TRIM** — no file imports it |
| `xgboost` | ML | Original scaffold — aspirational | **TRIM** — notebooks use RandomForest |
| `imbalanced-learn` | ML | Original scaffold — aspirational | **TRIM** |
| `kaleido` | Visualization | Plotly static image export | **KEEP IF** PDF generation uses `fig.write_image()` |
| `lxml` | Web Scraping | BS4 parser backend | **KEEP** — bs4 may use it as parser |
| `selenium` | Web Scraping | Original scaffold — aspirational | **TRIM** |
| `playwright` | Web Scraping | Original scaffold — aspirational | **TRIM** |
| `httpx` | Web Scraping | Original scaffold — async HTTP | **TRIM** |
| `langchain` | NLP/AI | Original scaffold — aspirational | **TRIM** |
| `transformers` | NLP/AI | Original scaffold — aspirational | **TRIM** — heavy install (2GB+) |
| `sentence-transformers` | NLP/AI | Original scaffold — aspirational | **TRIM** — heavy install |
| `gradio` | Web App | UI alternative | **TRIM** — Streamlit is the choice |
| `hubspot-api-client` | CRM | Listed but REST API used directly | **KEEP** — legitimate upgrade path |
| `google-auth` | Google APIs | May be transitive dep of `google-generativeai` | **INVESTIGATE** — may be needed |
| `google-api-python-client` | Google APIs | Original scaffold | **TRIM** — no `googleapiclient` import anywhere |
| `jupyter` | Notebook | Development tool | **MOVE** to dev dependencies |
| `ipywidgets` | Notebook | Development tool | **MOVE** to dev dependencies |
| `nbformat` | Notebook | Development tool | **MOVE** to dev dependencies |
| `pydantic` | Config | Original scaffold — aspirational | **TRIM** |
| `nltk` | Text Processing | Original scaffold — aspirational | **TRIM** |
| `spacy` | Text Processing | Original scaffold — aspirational | **TRIM** — heavy install (500MB+) |
| `textblob` | Text Processing | Original scaffold — aspirational | **TRIM** |
| `tqdm` | Utilities | Original scaffold | **TRIM** |
| `rich` | Utilities | Original scaffold | **TRIM** |
| `click` | Utilities | Original scaffold | **TRIM** |
| `loguru` | Utilities | Original scaffold | **TRIM** |
| `pytest-cov` | Testing | Not imported directly (pytest plugin) | **KEEP** — used by CI `--cov` flag |

### 5.3 Impact of Ghost Dependencies

Running `pip install -r requirements.txt` on a clean environment installs **all** of these, including:
- `transformers` (~2GB download + PyTorch dependency)
- `spacy` (~500MB)
- `playwright` (requires browser binaries)
- `xgboost` (C++ compilation may fail on some systems)

**Estimated clean install time with all ghosts:** 15-25 minutes
**Estimated clean install time with ghosts trimmed:** 2-3 minutes

A hiring manager running the Quick Start will encounter the long install. This is a significant UX risk.

---

## 6. File-by-File Review Status

### Source Code

| File | Stage 3 Action | Status | Issues |
|------|----------------|--------|--------|
| `src/clv_model.py` | NEW | Fixed (C1, C2) | M3 (ESSER fuzzy match) — deferred |
| `src/data_fetchers.py` | Unchanged | Reviewed | M16, M17, M18 — deferred |
| `src/researcher.py` | Unchanged | Not modified | — |
| `src/generate_territory_report.py` | Unchanged | Not modified | — |
| `src/visualization_theme.py` | Unchanged | Not modified | — |
| `data/run_data_collection.py` | Modified | Clean | m6 — minor |

### Streamlit App

| File | Stage 3 Action | Status | Issues |
|------|----------------|--------|--------|
| `07_streamlit_demo/app.py` | Unchanged | Not modified | — |
| `07_streamlit_demo/utils.py` | Unchanged | Reviewed | M12, M13, M15 — deferred |
| `pages/01_district_prioritizer.py` | Modified | Reviewed | M7, M9 — deferred |
| `pages/02_superintendent_intel.py` | Unchanged | Not modified | — |
| `pages/03_email_generator.py` | Unchanged | Not modified | — |
| `pages/04_pipeline_tracker.py` | Modified | Fixed (C3, M4, M5, M6) | m3, m4 — minor |
| `pages/05_battle_cards.py` | Unchanged | Not modified | — |
| `pages/06_deal_coach.py` | Unchanged | Not modified | — |

### Infrastructure

| File | Stage 3 Action | Status | Issues |
|------|----------------|--------|--------|
| `streamlit_app.py` | NEW → Rewritten | Fixed (C4, C5) | — |
| `.streamlit/config.toml` | NEW | Clean | — |
| `.github/workflows/ci.yml` | Unchanged | Reviewed | Python 3.10 vs badge 3.12+ |
| `requirements.txt` | Modified | Reviewed | 19+ ghost deps |
| `07_streamlit_demo/requirements.txt` | Modified | Fixed (X1) | — |

### Documentation

| File | Stage 3 Action | Status | Issues |
|------|----------------|--------|--------|
| `README.md` (root) | Modified | Reviewed | See §10 |
| `K-12-Sales-Toolkit/README.md` | Modified | Reviewed | See §10 |
| `STAGE2_REVIEW_REPORT.md` | Rewritten | Reviewed | Ghost dep undercount |
| `docs/WALKTHROUGH_SCRIPT.md` | NEW | Clean | — |

### Tests

| File | Stage 3 Action | Status | Issues |
|------|----------------|--------|--------|
| `tests/test_district_scoring.py` | Unchanged | Reviewed | 12 test methods, `scrape_eddata_profile` hits live API |

---

## 7. Notebook Validity

| Notebook | JSON Valid | Stale Outputs | sys.path Fixed | CSV Fallback |
|----------|-----------|---------------|----------------|--------------|
| `california_district_prioritization_model.ipynb` | YES | CLEARED (was 4 cells) | YES | YES (2025→2024) |
| `la_unified_opportunity_analysis.ipynb` | YES | CLEAN | YES | YES (2025→2024) |
| `literacy_partners_competitive_positioning.ipynb` | YES | Has outputs | YES | N/A |
| `discovery_call_prep_dashboard.ipynb` | YES | Has outputs | YES | N/A |
| `hubspot_pipeline_health_analyzer.ipynb` | YES | Has outputs | YES | N/A |
| `k12_sales_is_different_heres_how.ipynb` | YES | Has outputs | YES | N/A |
| `solving_teacher_buy_in_challenge.ipynb` | YES | Has outputs | YES | N/A |
| `teacher_to_sales_my_journey.ipynb` | YES | Has outputs | YES | N/A |
| `my_first_90_days_plan.ipynb` | YES | Has outputs | YES | N/A |

All 9 notebooks parse as valid JSON. The 7 non-district-intelligence notebooks retain their original outputs (which are case study content, not stale data artifacts — acceptable for portfolio presentation).

---

## 8. Testing & CI Status

### CI Configuration (`.github/workflows/ci.yml`)

- **Python version:** 3.10 (but README badge says 3.12+)
- **Install:** `pip install -r K-12-Sales-Toolkit/requirements.txt` — this installs ALL ghost dependencies, making CI slow
- **Tests:** `pytest K-12-Sales-Toolkit/tests/ -v --tb=short --cov`
- **Smoke test:** `timeout 10 streamlit run app.py` — 10 second health check

### Test Coverage

- 12 test methods across 5 test classes
- `TestEdDataScraper` hits a live API (ed-data.org) — will fail if site is down
- `TestScoringLogic` uses `pytest.skip` on ImportError — a broken `utils.py` would silently skip, not fail

### Recommended CI Improvements

1. Separate `requirements-dev.txt` for ghost deps to speed up CI
2. Mock the Ed-Data API call in tests
3. Change `pytest.skip` to `pytest.fail` for import errors (or use `importorskip` with clear messaging)

---

## 9. Streamlit Cloud Deployment Readiness

### Configuration

| Item | Status | Detail |
|------|--------|--------|
| Entrypoint file | `streamlit_app.py` at repo root | Uses `importlib.util` (safe) |
| Theme config | `.streamlit/config.toml` | LP brand colors |
| Requirements | `07_streamlit_demo/requirements.txt` | 11 packages including `lifetimes` |
| Environment secrets | `HUBSPOT_API_KEY`, `GEMINI_API_KEY` | Must be set in Streamlit Cloud secrets |

### Known Deployment Risks

1. **`sys.path` manipulation** — The entrypoint adds `_DEMO`, `_TOOLKIT`, and `_SRC` to `sys.path`. This works but is fragile. If Streamlit Cloud changes working directory behavior, imports break.
2. **`data/processed/` CSV files** — Must be committed to the repo. Streamlit Cloud runs from the repo directly.
3. **No `.streamlit/secrets.toml` in repo** — Correct (secrets must be configured in the Cloud UI), but new deployers may not know this.
4. **`beautifulsoup4` not in Streamlit requirements** — If any Streamlit page path triggers a `data_fetchers` import, it will crash. Currently this doesn't happen, but it's a latent risk.

### Deployment Checklist

- [ ] Set `GEMINI_API_KEY` in Streamlit Cloud secrets (required for Superintendent Intel, Email Generator, Deal Coach)
- [ ] Set `HUBSPOT_API_KEY` in Streamlit Cloud secrets (optional — falls back to demo data)
- [ ] Verify all CSV files in `data/processed/` are committed
- [ ] Test deployment with Streamlit Cloud's build logs to catch any missing dependencies

---

## 10. README & Documentation Gaps

### CRITICAL — Must Fix Before Push

| Issue | File | Detail |
|-------|------|--------|
| **Placeholder contact info** | Both READMEs | `[your.email@gmail.com]`, `[LinkedIn Profile URL]`, `[AetherBlog Portfolio URL]` are still unfilled. A hiring manager will see this. |
| **Dead "Watch on Loom" link** | Root README | Points to `docs/WALKTHROUGH_SCRIPT.md` (a local file), not an actual Loom video URL. Label says "Watch on Loom" which is misleading. |
| **Dead "Open in Colab" links** | Both READMEs | All `#` anchor links. Either create real Colab links or remove. |
| **Dead "View on AetherBlog" links** | Inner README | All `#` anchor links. |

### MODERATE — Should Fix

| Issue | File | Detail |
|-------|------|--------|
| Python version mismatch | README badge vs CI | Badge says 3.12+, CI uses 3.10 |
| `clv_model.py` missing from tree | Both READMEs | `src/` tree diagram omits this key new file |
| `streamlit_app.py` missing from tree | Root README | Repo root file not shown |
| `hubspot-api-client` claim | Both READMEs | Tech stack says "hubspot-api-client (pipeline tracker integration)" but the SDK is never imported — `requests` is used directly |
| Page count "6 pages" | STAGE2_REVIEW_REPORT | Lists 7 items (Home + 6 subpages) but says "6 pages" |
| Ghost dep count "12" | STAGE2_REVIEW_REPORT | Actual count is 19+ unused packages |

---

## 11. Action Items for Dev Team

### Priority 1 — Before Push (Critical)

- [ ] **Fill in contact information** in both READMEs (email, LinkedIn, portfolio URL)
- [ ] **Decide on dead links:** Either create real Colab/Loom/AetherBlog URLs or remove the placeholder rows
- [ ] **Test `clv_model.py`** — run `compute_clv()` with the real CAASPP 2025 data and verify output
- [ ] **Test pipeline tracker** with a real HubSpot API key (or verify demo mode is acceptable)
- [ ] **Run full test suite:** `pytest K-12-Sales-Toolkit/tests/ -v` and verify 12/12 pass

### Priority 2 — Before Push (Recommended)

- [ ] **Trim ghost dependencies** — Remove the 19 unused packages from `requirements.txt` to reduce install time from 15min to 2min. Create a `requirements-roadmap.txt` for aspirational packages.
- [ ] **Fix Python version badge** — Change to 3.10+ (matching CI) or update CI to 3.12
- [ ] **Update README tree diagrams** — Add `src/clv_model.py`, `streamlit_app.py`
- [ ] **Fix FRPM aggregation** in `utils.py:285` — Change `"first"` to `"sum"` for enrollment columns

### Priority 3 — Nice to Have

- [ ] Add `__init__.py` to `src/` for proper package imports
- [ ] Mock the Ed-Data API call in tests to avoid flaky CI
- [ ] Add `beautifulsoup4` to Streamlit demo requirements (latent crash risk)
- [ ] Normalize CAASPP column names with `.str.strip().str.lower()` after CSV read

---

## 12. Zip Package Contents

The accompanying `STAGE3_REVIEW_PACKAGE.zip` contains **only** the files necessary for dev team review and testing. No binary artifacts, cached outputs, IDE config, or redundant copies.

```
STAGE3_REVIEW_PACKAGE/
├── STAGE3_EXEC_REVIEW.md          # This document
├── .github/
│   └── workflows/
│       └── ci.yml                 # CI/CD configuration
├── .streamlit/
│   └── config.toml                # Streamlit Cloud theme
├── streamlit_app.py               # Streamlit Cloud entrypoint
├── K-12-Sales-Toolkit/
│   ├── README.md                  # Inner README
│   ├── requirements.txt           # Python dependencies
│   ├── STAGE2_REVIEW_REPORT.md    # Review report (rewritten)
│   ├── 01_district_intelligence/
│   │   ├── california_district_prioritization_model.ipynb
│   │   └── la_unified_opportunity_analysis.ipynb
│   ├── 02_competitive_research/
│   │   └── literacy_partners_competitive_positioning.ipynb
│   ├── 03_outreach_automation/
│   │   ├── personalized_email_generator.py
│   │   └── superintendent_research_engine.ipynb
│   ├── 04_sales_cycle_tools/
│   │   ├── discovery_call_prep_dashboard.ipynb
│   │   └── hubspot_pipeline_health_analyzer.ipynb
│   ├── 05_case_studies/
│   │   ├── k12_sales_is_different_heres_how.ipynb
│   │   ├── solving_teacher_buy_in_challenge.ipynb
│   │   ├── teacher_to_sales_my_journey.ipynb
│   ├── 06_literacy_partners_custom/
│   │   └── my_first_90_days_plan.ipynb
│   ├── 07_streamlit_demo/
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   ├── utils.py
│   │   └── pages/
│   │       ├── 01_district_prioritizer.py
│   │       ├── 02_superintendent_intel.py
│   │       ├── 03_email_generator.py
│   │       ├── 04_pipeline_tracker.py
│   │       ├── 05_battle_cards.py
│   │       └── 06_deal_coach.py
│   ├── data/
│   │   ├── run_data_collection.py
│   │   └── processed/
│   │       ├── caaspp_ela_2024.csv
│   │       ├── caaspp_ela_2025.csv
│   │       ├── esser_grants_ca.csv
│   │       └── la_metro_districts.csv
│   ├── docs/
│   │   └── WALKTHROUGH_SCRIPT.md
│   ├── src/
│   │   ├── clv_model.py
│   │   ├── data_fetchers.py
│   │   ├── generate_territory_report.py
│   │   ├── researcher.py
│   │   └── visualization_theme.py
│   └── tests/
│       └── test_district_scoring.py
├── README.md                      # Root README
```

**Excluded from zip:**
- `__pycache__/`, `.ipynb_checkpoints/`, `.pytest_cache/` — build artifacts
- `assets/`, `reports/` — generated output (not source)
- `*.zip` — nested archives
- `*.txt` (streamlit_err, streamlit_out) — debug logs
- `*.png` (district_prioritization_matrix) — generated chart
- `*.csv` (top_priority_districts) — generated output
- `DO-NOT-COMMIT` — explicitly excluded
- `.env` — secrets file
- `CHANGES_SUMMARY.md`, `JULES_DIRECTIVE.md`, `JULES_INSTRUCTIONS.md` — internal process docs
- `science_of_reading_adoption_tracker.py` — standalone utility, not core

---
Ishmael Muhammad, 240-739-8914, i.mm0904@gmail.com, https://www.linkedin.com/in/ishmael-muhammad-93806925a/  https://runforme.app/aetherblog/ , loom link pending, colab links pending, we will adress ghost dependencies at the very very end. leave it for now.
*End of Stage 3 Executive Review*
