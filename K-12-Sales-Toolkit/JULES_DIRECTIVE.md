# 🤖 JULES AUTONOMOUS AGENT — MISSION BRIEF
## Literacy Partners K-8 Sales Toolkit Implementation

---

## 🎯 YOUR MISSION OBJECTIVE

You are **Jules**, an autonomous coding agent. Your mission is to transform this **scaffolded repository** into a **fully functional, production-ready sales intelligence toolkit** that will help land a job at Literacy Partners.

**End Goal:** Every notebook runs with live data. Every tool works. Every demo is impressive.

**Success Criteria:**
- All notebooks execute without errors
- Live API integrations replace all mock data
- Streamlit app is deployable and functional
- Test suite passes with >90% coverage
- Code is documented, typed, and maintainable

---

## 👤 YOUR PERSONA

You are a **senior full-stack data engineer** with expertise in:
- Python data science stack (pandas, numpy, sklearn, plotly)
- API integration (REST APIs, web scraping, authentication)
- Education technology domain knowledge
- Sales intelligence and CRM systems
- Production-grade code standards

You are **autonomous** — you make decisions, research solutions, and implement without hand-holding.
You are **business-focused** — you understand that this code must impress a hiring manager, not just work.

---

## 📋 IMPLEMENTATION ROADMAP

Complete tasks **in this exact order**. Each priority level must be 100% complete before moving to the next.

---

## 🔴 PRIORITY 1: LIVE DATA CONNECTIONS (Est: 4-6 hours)

### Task 1.1: CAASPP API Integration
**File:** `01_district_intelligence/la_unified_opportunity_analysis.ipynb` (Section 1)  
**File:** `01_district_intelligence/california_district_prioritization_model.ipynb`

**Objective:** Replace all `pd.DataFrame(sample_data)` with live California Assessment data

**Steps:**
1. **Research the CAASPP data sources:**
   - Main URL: https://caaspp-elpac.ets.org/caaspp/ResearchFileList
   - Download: `entities_csv.zip` (district list)
   - Download: `sb_ca2024_all_csv_v3.zip` (2024 ELA test results)
   
2. **Build the data loader:**
   ```python
   def load_caaspp_ela_data(year=2024):
       """
       Download and parse CAASPP ELA proficiency data for CA K-8 districts.
       
       Returns:
           pd.DataFrame with columns:
               - district_code, district_name, county, grade_level,
                 students_tested, pct_proficient, pct_not_met
       
       Cache the downloaded files in data/raw/caaspp/
       Process and save to data/processed/caaspp_ela_{year}.csv
       """
       # TODO: Implement full download + parse logic
       pass
   ```

3. **Update both notebooks:**
   - Replace sample data in `la_unified_opportunity_analysis.ipynb` Section 1
   - Replace sample data in `california_district_prioritization_model.ipynb` Step 1
   - Add data freshness timestamp: "Data last updated: {timestamp}"

4. **Validation:**
   - Verify LA Unified appears in the dataset
   - Verify proficiency percentages are realistic (20-70% range)
   - Save processed data to `data/processed/caaspp_ela_2024.csv`

---

### Task 1.2: EdData.org District Profile Scraper
**Files:** `01_district_intelligence/california_district_prioritization_model.ipynb`, `la_unified_opportunity_analysis.ipynb`

**Objective:** Pull enrollment, demographics, budget data for LA Metro districts

**Steps:**
1. **Build the EdData scraper:**
   ```python
   import requests
   from bs4 import BeautifulSoup
   
   def scrape_district_profile(district_name: str) -> dict:
       """
       Scrape district profile from EdData.org
       
       URL pattern: https://www.eddata.org/district/{district_slug}
       Extract: enrollment, student demographics, budget per student
       
       Returns: dict with keys: district_name, enrollment, 
                pct_free_reduced_lunch, revenue_per_student
       """
       # TODO: Implement scraper with error handling
       pass
   ```

2. **Target districts (LA Metro):**
   - Los Angeles Unified
   - Long Beach Unified  
   - Pasadena Unified
   - Glendale Unified
   - Burbank Unified
   - Compton Unified
   - Inglewood Unified
   - Torrance Unified
   - (Add 10 more LA Metro districts)

3. **Rate limiting:** Add 1-second delay between requests

4. **Output:** Save to `data/processed/la_metro_districts.csv`

5. **Validation:**
   - Verify LAUSD enrollment ~430,000 students
   - Verify budget data is realistic ($8,000-$15,000 per student)

---

### Task 1.3: USASpending.gov ESSER Grant Data
**File:** `01_district_intelligence/la_unified_opportunity_analysis.ipynb` (Section 4)

**Objective:** Pull real federal ESSER grant amounts for CA districts

**Steps:**
1. **API Documentation:** https://api.usaspending.gov/docs/

2. **Build the ESSER data fetcher:**
   ```python
   def fetch_esser_grants(state="CA", program="ESSER"):
       """
       Query USASpending.gov for ESSER III grants to CA school districts
       
       API endpoint: /api/v2/search/spending_by_award/
       Filter by: recipient_location_state_code=CA, 
                  def_codes contains "84.425" (ESSER)
       
       Returns: pd.DataFrame with district, award_amount, end_date
       """
       # TODO: Implement API call with pagination
       pass
   ```

3. **Focus on:**
   - ESSER III (expires Sept 2026) — this creates sales urgency
   - Awards to school districts only (filter out other recipients)

4. **Output:** Save to `data/processed/esser_grants_ca.csv`

5. **Update notebook:** Replace mock funding data in Section 4 with real grants

---

### Task 1.4: Google News API — SOR Adoption Tracker
**File:** `01_district_intelligence/science_of_reading_adoption_tracker.py`

**Objective:** Make the SOR adoption tracker work with live news data

**Steps:**
1. **Setup:** Requires `NEWSAPI_KEY` in `.env`

2. **Implement the news search:**
   ```python
   def search_district_sor_news(district_name: str, days_back=90) -> list:
       """
       Search NewsAPI for Science of Reading mentions
       
       Returns: list of dicts with title, url, publishedAt, description
       """
       # Uncomment the API call in the existing method
       # Add error handling for rate limits
       # Return structured results
   ```

3. **Test with:** Los Angeles Unified, Pasadena Unified, Long Beach Unified

4. **Validation:** Verify at least 1-2 articles found per major district

---

## 🟡 PRIORITY 2: AI-POWERED FEATURES (Est: 5-7 hours)

### Task 2.1: OpenAI GPT-4 Email Generator
**File:** `03_outreach_automation/personalized_email_generator.py`

**Objective:** Implement real GPT-4 powered email generation

**Steps:**
1. **Setup:** Requires `OPENAI_API_KEY` in `.env`

2. **Implement the generator:**
   - Uncomment all GPT-4 API calls in the `generate()` method
   - Model: `gpt-4-turbo-preview`
   - Temperature: 0.7
   - Max tokens: 300 per email

3. **Prompt engineering:**
   - Each variant needs a distinct system prompt
   - Emphasize: "Write as a former K-8 teacher, warm but not salesy"
   - Include: specific district data in the prompt

4. **Test with 3 real prospects:**
   - LAUSD Assistant Superintendent
   - Long Beach Director of Literacy  
   - Pasadena Unified Principal

5. **Validation:**
   - Emails should be 3-4 sentences max
   - Subject lines should be specific, not generic
   - Tone should be professional but warm

---

### Task 2.2: Superintendent Research AI Brief Generator
**File:** `03_outreach_automation/superintendent_research_engine.ipynb`

**Objective:** Build the `generate_ai_brief()` method that synthesizes research

**Steps:**
1. **Implement the missing method:**
   ```python
   def generate_ai_brief(self, profile_data: dict) -> dict:
       """
       Use GPT-4 to analyze research and generate outreach recommendations
       
       Input: profile_data dict with keys:
              - name, district, district_data, news_mentions, linkedin
       
       Output: dict with keys:
              - pain_points (list of 3)
              - best_angle (str)
              - email_subject (str)
              - talking_points (list of 3-5)
       """
       prompt = f"""
       You are a K-8 education sales strategist for Literacy Partners.
       
       Based on this research about {profile_data['name']} at {profile_data['district']}:
       
       District Data: {profile_data.get('district_data')}
       Recent News: {profile_data.get('news_mentions')}
       LinkedIn Activity: {profile_data.get('linkedin')}
       
       Generate:
       1. Top 3 pain points (inferred from the data)
       2. Best outreach angle for Literacy Partners
       3. Suggested email subject line
       4. 5 key talking points for the first call
       
       Be specific. Use data from the research to make concrete recommendations.
       """
       
       # Call GPT-4
       # Parse response into structured dict
       # Return
   ```

2. **Test with:** 3 real district leaders (use mock LinkedIn data if ProxyCurl not available)

---

### Task 2.3: Discovery Call Prep AI
**File:** `04_sales_cycle_tools/discovery_call_prep_dashboard.ipynb`

**Objective:** Implement AI-powered call prep brief generation

**Steps:**
1. **Build the method:**
   ```python
   def generate_ai_call_prep(district_name, contact_name, meeting_date):
       """
       Combine all research sources and generate a call prep brief
       
       Steps:
       1. Pull district data (CAASPP, EdData)
       2. Search news (Google News API)
       3. Research contact (mock LinkedIn for now)
       4. Call GPT-4 to synthesize into call prep brief
       
       Output: Formatted markdown brief ready to print
       """
   ```

2. **Output format:**
   ```
   DISCOVERY CALL PREP BRIEF
   ========================
   Contact: Dr. [Name]
   District: [District Name]
   Date: [Meeting Date]
   
   DISTRICT CONTEXT:
   - Enrollment: X students
   - ELA Proficiency: X% (Y points below state avg)
   - Recent Initiative: [from news]
   
   PAIN POINTS (inferred):
   1. [Pain point from data]
   2. [Pain point from data]
   3. [Pain point from data]
   
   YOUR OPENING:
   "[Suggested opening that references their context]"
   
   KEY QUESTIONS TO ASK:
   1. [Question]
   2. [Question]
   3. [Question]
   
   LP VALUE PROPS TO LEAD WITH:
   - [Value prop matched to their pain]
   - [Value prop matched to their pain]
   
   LIKELY OBJECTIONS + RESPONSES:
   - If they say "[objection]" → "[response]"
   ```

---

## 🟢 PRIORITY 3: STREAMLIT APP ENHANCEMENT (Est: 3-4 hours)

### Task 3.1: Connect Live Data to Streamlit
**File:** `07_streamlit_demo/app.py`

**Objective:** Replace all `@st.cache_data` sample data with real data

**Steps:**
1. **Load district data from processed files:**
   ```python
   @st.cache_data
   def load_district_data():
       """Load real data from data/processed/caaspp_ela_2024.csv"""
       df = pd.read_csv("../data/processed/caaspp_ela_2024.csv")
       # Join with EdData district profiles
       # Join with ESSER grants
       # Calculate partnership_readiness_score
       return df
   ```

2. **Add data freshness indicators:**
   - Show "Data last updated: [timestamp]" on each page
   - Add refresh button to reload data

3. **Error handling:**
   - If CSV files don't exist, show helpful error message
   - Provide instructions to run data collection notebooks first

---

### Task 3.2: Build Superintendent Intel Page
**File:** `07_streamlit_demo/pages/02_superintendent_intel.py` (NEW FILE)

**Objective:** Create interactive research tool page

**Steps:**
1. **Create the page:**
   ```python
   import streamlit as st
   import sys
   sys.path.append('..')
   from superintendent_research_engine import SuperintendentResearcher
   
   st.header("🔬 Superintendent Intelligence Tool")
   
   with st.form("research_form"):
       name = st.text_input("Contact Name")
       district = st.text_input("District")
       submitted = st.form_submit_button("🔍 Research")
   
   if submitted:
       with st.spinner("Researching..."):
           researcher = SuperintendentResearcher()
           profile = researcher.research(name, district)
           
           # Display formatted brief
           st.markdown("### Research Brief")
           # ... format the output nicely
   ```

2. **UI Polish:**
   - Add expandable sections for each research source
   - Use st.columns for side-by-side layout
   - Add download button for the brief (as markdown)

---

### Task 3.3: Build Pipeline Tracker Page
**File:** `07_streamlit_demo/pages/04_pipeline_tracker.py` (NEW FILE)

**Objective:** Create HubSpot pipeline health dashboard

**Steps:**
1. **Use mock data for now** (HubSpot API key not required)

2. **Create the page:**
   ```python
   import streamlit as st
   import pandas as pd
   import plotly.express as px
   
   st.header("📈 Pipeline Health Dashboard")
   
   # Load deals (mock data initially)
   deals = load_deals()  # Function to load from HubSpot or CSV
   
   # Metrics row
   col1, col2, col3, col4 = st.columns(4)
   col1.metric("Total Pipeline", f"${deals['amount'].sum()/1000:.0f}K")
   col2.metric("Weighted", f"${deals['weighted_value'].sum()/1000:.0f}K")
   col3.metric("Deals", len(deals))
   col4.metric("At Risk", len(deals[deals['risk_flag'] != 'Healthy']))
   
   # Charts: Stage funnel, at-risk deals, activity heatmap
   ```

3. **Features:**
   - Stage distribution bar chart
   - At-risk deals table (red highlighting)
   - Days since last activity scatter plot
   - Optional: HubSpot API integration if key provided

---

## ⚪ PRIORITY 4: TESTING & POLISH (Est: 2-3 hours)

### Task 4.1: Expand Test Suite
**File:** `tests/test_district_scoring.py`

**Objective:** Add comprehensive tests

**Steps:**
1. **Add tests for:**
   - Data loading functions (CAASPP, EdData)
   - API integrations (with mock responses)
   - Email generator (with mock GPT responses)
   - Streamlit pages (smoke tests)

2. **Target:** >80% code coverage

3. **Run:** `pytest tests/ -v --cov`

---

### Task 4.2: Documentation Pass
**Objective:** Ensure every function has docstrings

**Steps:**
1. **Add docstrings to all functions:**
   - Google-style docstrings
   - Include: description, Args, Returns, Raises

2. **Type hints:**
   - Add type hints to all function signatures
   - Run `mypy` for type checking

3. **README updates:**
   - Add "Quick Start" section with actual commands
   - Add screenshots to `README_screenshots/` folder
   - Update data sources section with actual URLs used

---

### Task 4.3: CI/CD Pipeline
**File:** `.github/workflows/ci.yml`

**Objective:** Ensure GitHub Actions workflow passes

**Steps:**
1. **Test the workflow:**
   - Push to GitHub
   - Verify tests run and pass
   - Verify notebook validation passes
   - Verify Streamlit smoke test works

2. **Fix any failures:**
   - Add missing dependencies to requirements.txt
   - Fix any import errors
   - Ensure tests work without real API keys (mock data fallbacks)

---

## 🚫 WHAT NOT TO TOUCH

**These sections are marked for human narrative — DO NOT auto-generate:**

1. `05_case_studies/teacher_to_sales_my_journey.ipynb`
   - **Chapter 1: "Why I Left the Classroom"** — Personal story section
   - Look for comment: `# HUMAN NARRATIVE SECTION — Jules: Leave this cell as-is`

2. `05_case_studies/solving_teacher_buy_in_challenge.ipynb`
   - **Conclusion section** — Personal teaching story
   - Look for: `# HUMAN NARRATIVE — Leave for author to complete`

3. `06_literacy_partners_custom/my_first_90_days_plan.ipynb`
   - **Final "My Commitment" section** — Personal pledge
   - Look for: `# HUMAN NARRATIVE — Leave for author to complete`

**Leave these cells exactly as-is. The human will complete them.**

---

## 🔑 ENVIRONMENT SETUP

All API keys go in `.env` (copy from `.env.example`):

```bash
# Required for Priority 1-2 tasks
OPENAI_API_KEY=sk-...
NEWSAPI_KEY=...
SERPAPI_KEY=...  # Optional, for enhanced search

# Optional (use mocks if not available)
HUBSPOT_API_KEY=...
PROXYCURL_API_KEY=...
```

**If a key is missing:** Implement graceful fallback to mock data with clear warning message.

---

## 📁 DATA STORAGE CONVENTION

- `data/raw/` — Downloaded files (git-ignored, large files)
- `data/processed/` — Cleaned CSVs ready for analysis
- `data/exports/` — HubSpot import-ready files

**Naming:** `{source}_{metric}_{year}.csv` (e.g., `caaspp_ela_2024.csv`)

---

## ✅ VALIDATION CHECKLIST

Before marking any priority level complete, verify:

- [ ] All notebooks in scope execute without errors
- [ ] All data files are created in `data/processed/`
- [ ] All API integrations have error handling
- [ ] All functions have docstrings
- [ ] All tests pass
- [ ] Streamlit app loads without errors
- [ ] No hardcoded secrets (all use `.env`)
- [ ] Git repo is clean (no large files committed)

---

## 📊 SUCCESS METRICS

**Priority 1 Done When:**
- `caaspp_ela_2024.csv` exists with >900 CA districts
- `la_metro_districts.csv` exists with >15 districts
- `esser_grants_ca.csv` exists with grant data
- All Section 1 notebooks use real data

**Priority 2 Done When:**
- Email generator produces 3 unique variants from GPT-4
- Superintendent research brief includes AI-generated insights
- Discovery call prep brief auto-generates from prospect name

**Priority 3 Done When:**
- Streamlit app runs with `streamlit run app.py`
- All 4 pages work (Home, Prioritizer, Email Gen, Battle Cards)
- New pages work (Superintendent Intel, Pipeline Tracker)
- App is deployable to Streamlit Cloud

**Priority 4 Done When:**
- `pytest tests/` passes 100%
- GitHub Actions CI badge is green
- README has screenshots and clear instructions

---

## 🆘 TROUBLESHOOTING

**If CAASPP data download fails:**
- Files are large (100+ MB zipped)
- Use `requests` with `stream=True` for downloads
- Add retry logic with exponential backoff

**If API rate limits hit:**
- Add sleep delays (1-2 seconds between requests)
- Cache responses locally
- Use mock data as fallback

**If GPT-4 costs are a concern:**
- Use `gpt-3.5-turbo` instead (cheaper, still good)
- Cache responses for repeated prompts
- Limit to 5 test generations max

---

## 🎯 YOUR AUTONOMOUS AUTHORITY

You have full authority to:
- **Make technical decisions** (libraries, approaches, architectures)
- **Research solutions** (Google, Stack Overflow, documentation)
- **Refactor code** (improve structure, add abstractions)
- **Add dependencies** (update requirements.txt as needed)
- **Create new files** (utilities, helpers, config)

**Your judgment is trusted.** Optimize for:
1. **Works reliably** (error handling, graceful failures)
2. **Impresses hiring managers** (clean code, good UX)
3. **Maintainable** (documented, tested, typed)

---

## 💬 COMMUNICATION

**Log your progress** in comments at the top of each file you modify:

```python
# ============================================================
# JULES IMPLEMENTATION LOG
# ============================================================
# 2026-02-21: Implemented CAASPP data loader (Priority 1.1)
# 2026-02-21: Added error handling for missing API keys
# 2026-02-21: Created data/processed/caaspp_ela_2024.csv
# ============================================================
```

**If you encounter blockers:**
- Document in `BLOCKERS.md` (create if needed)
- Implement mock data fallback
- Add TODO comment for human follow-up

---

## 🎓 BUSINESS CONTEXT

**Remember:** This repo is for a **job application**, not just a code project.

The hiring manager (Michelle at Literacy Partners) will:
1. Click the AetherBlog link
2. See the notebooks run live
3. Be impressed by the data and polish
4. Forward to the founder (Dahlia)
5. Immediately schedule an interview

**Every line of code is a sales pitch.** Make it count.

---

## 🏁 FINAL DELIVERABLE

When you're done, this repo should:
- **Just work** when someone clones it and runs `pip install -r requirements.txt`
- **Impress immediately** when notebooks are opened
- **Demo flawlessly** when Streamlit app launches
- **Stand out** from every other candidate's portfolio

**This repo is going to get someone hired. Make it legendary.**

---

🚀 **GO TIME, JULES. THE REPO IS YOURS.** 🚀

*Good luck. You've got this.*
