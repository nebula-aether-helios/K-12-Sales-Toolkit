# 🤖 JULES AGENT INSTRUCTIONS
## Autonomous Coding Agent — Implementation Guide

---

Welcome, Jules! This file tells you exactly what to build.  
The repo scaffold is complete. Your job is to make every TODO real.

---

## 🎯 Your Mission

This is a **sales intelligence portfolio** for a job application to  
**Literacy Partners** (Sales Executive, K-8 Partnerships).  
The tools here need to actually WORK — not just be stubs.

Priority: Build things that impress a **hiring manager**, not just a developer.  
Business logic matters as much as technical correctness.

---

## 📋 Priority Queue (Top → Bottom)

### 🔴 PRIORITY 1: Live Data Connections (3-4 hours)

**Task 1.1: CAASPP API Integration**
- File: `01_district_intelligence/la_unified_opportunity_analysis.ipynb` (Section 1)
- API: `https://caaspp-elpac.ets.org/caaspp/ResearchFileList`
- Goal: Replace all `pd.DataFrame(sample_data)` with live API calls
- Notes: Download CSV files from CAASPP, parse, and store in `data/` folder

**Task 1.2: EdData.org District Scraper**
- File: `01_district_intelligence/california_district_prioritization_model.ipynb`
- URL: `https://www.eddata.org/district/` + district slug
- Goal: Pull real enrollment, budget, demographics for all LA Metro districts
- Store as: `data/la_metro_districts.csv`

**Task 1.3: USASpending.gov ESSER Data**
- File: `01_district_intelligence/la_unified_opportunity_analysis.ipynb` (Section 4)
- API: `https://api.usaspending.gov/api/v2/search/spending_by_award/`
- Query: Filter by recipient = "school district", award type = "grant", keyword = "ESSER"
- Goal: Pull real ESSER III grant amounts per CA district

---

### 🟡 PRIORITY 2: AI Feature Implementation (4-5 hours)

**Task 2.1: OpenAI Email Generator**
- File: `03_outreach_automation/personalized_email_generator.py`
- Action: Implement the `generate()` method with real GPT-4 call
- Model: `gpt-4-turbo-preview`
- Requires: `OPENAI_API_KEY` in `.env`
- Test with: the 3 sample prospects in `if __name__ == "__main__":` block

**Task 2.2: Superintendent Research AI Brief**
- File: `03_outreach_automation/superintendent_research_engine.ipynb`
- Action: Implement `generate_ai_brief()` method
- Input: district name + contact name
- Output: formatted research brief (pain points, outreach angles, suggested subject)

**Task 2.3: Discovery Call Prep AI**
- File: `04_sales_cycle_tools/discovery_call_prep_dashboard.ipynb`
- Action: Implement `generate_ai_brief()` on `DiscoveryCallPrepEngine`
- Integrate with: superintendent_research_engine.ipynb output

---

### 🟢 PRIORITY 3: Streamlit App Polish (2-3 hours)

**Task 3.1: Connect Live Data to Streamlit**
- File: `07_streamlit_demo/app.py`
- Replace: all `@st.cache_data` sample data with real data from `data/` CSVs
- Add: loading spinners, error handling, "data last updated" timestamps

**Task 3.2: Add Superintendent Intel Page**
- File: `07_streamlit_demo/pages/02_superintendent_intel.py` (create new)
- Input: District name + contact name
- Output: Formatted research brief from `superintendent_research_engine.ipynb`

**Task 3.3: Add Pipeline Tracker Page**
- File: `07_streamlit_demo/pages/04_pipeline_tracker.py` (create new)
- Connect to: HubSpot API (use mock data if no API key)
- Show: at-risk deals, stage distribution, activity heatmap

---

### ⚪ PRIORITY 4: Testing & Documentation (1-2 hours)

**Task 4.1: Basic Tests**
- Create: `tests/test_district_scoring.py`
- Test: `score_district()` function from `california_district_prioritization_model.ipynb`
- Test: `PilotReadinessScorecard.score()` from `solving_teacher_buy_in_challenge.ipynb`

**Task 4.2: GitHub Actions CI**
- Create: `.github/workflows/ci.yml`
- Run: `pytest tests/` on every push
- Run: `streamlit run 07_streamlit_demo/app.py --server.headless=true` smoke test

---

## 🔑 Environment Setup

All API keys are in `.env.example`. Copy to `.env` before starting.  
Keys needed for Priority 1-2 tasks:
- `OPENAI_API_KEY` — OpenAI GPT-4
- `SERPAPI_KEY` — Google Search (for superintendent research)
- `NEWSAPI_KEY` — News mentions (for SOR adoption tracker)

No keys needed for Priority 3-4 (mock data fallbacks built in).

---

## 📁 Data Storage Convention

- Raw data: `data/raw/` (never commit large files — add to .gitignore)
- Processed data: `data/processed/`
- Exports: `data/exports/` (CSV files for HubSpot import)

---

## ⚠️ What NOT to Touch

These sections are **marked for human narrative** — DO NOT auto-generate:
- `05_case_studies/teacher_to_sales_my_journey.ipynb` — Chapter 1 (personal story)
- `06_literacy_partners_custom/my_first_90_days_plan.ipynb` — Final commitment section
- `05_case_studies/solving_teacher_buy_in_challenge.ipynb` — Conclusion section

These cells have the comment: `# HUMAN NARRATIVE SECTION — Jules: Leave this cell as-is`

---

## 📞 Questions?

If something is ambiguous, default to:
1. More business context > less (explain WHY, not just what the code does)
2. Working mock data > broken live data
3. Comments explaining TODOs > silent stubs

---

*Happy coding, Jules! This repo is going to get someone hired.* 🚀
