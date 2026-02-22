[README.md](https://github.com/user-attachments/files/25462869/README.md)
# 📚 K-8 Sales Intelligence Toolkit
### Built for Literacy Partners | By a Former Teacher + SDR + Data Scientist

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-Live%20Demo-red.svg)](https://streamlit.io)
[![Notebooks](https://img.shields.io/badge/Notebooks-AetherBlog-purple.svg)](https://runforme.app/aetherblog/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Literacy Partners](https://img.shields.io/badge/Built%20For-Literacy%20Partners-orange.svg)](https://literacypartners.com)

---

> *"I didn't just apply for this role. I built the tools I'd use on day one."*

---

## 🚀 Live Demo

| Resource | Link |
|----------|------|
| 📓 Interactive Notebooks | [AetherBlog Portfolio →](https://runforme.app/aetherblog/) |
| 🎯 LA Unified Analysis | [View Live Notebook →](https://runforme.app/aetherblog/) |
| 🖥️ Streamlit Dashboard | [Try District Intelligence Tool →](#) |
| 🎥 60-Second Walkthrough | [Watch Loom Video →](#) |

---

## 👤 Who Built This

I'm a **former K-8 teacher** turned **top-10% SDR** who discovered that the intersection of
education experience and data science creates an unfair sales advantage.

**My Stack:**
- 🍎 5 years K-8 classroom teacher (I speak your buyers' language)
- 📞 2 years SDR (134% of quota, built automated prospecting tools)
- 🐍 Python + data science (I build tools that 10x rep efficiency)

**Why this repo exists:**  
Most sales candidates send a resume. I send working tools. Every notebook here solves a
real problem that K-12 education sales teams face every day. This is how I work.

---

## 🗂️ Repo Structure

```
literacy-partners-k8-sales-toolkit/
│
├── 📊 01_district_intelligence/        # OPTION A: Account Scoring + Territory Intel
│   ├── la_unified_opportunity_analysis.ipynb       ⭐ THE FLAGSHIP
│   ├── california_district_prioritization_model.ipynb
│   ├── literacy_budget_trend_analyzer.ipynb
│   └── science_of_reading_adoption_tracker.py
│
├── 🔍 02_competitive_research/          # Market Intelligence + Positioning
│   ├── pd_provider_landscape_analysis.ipynb
│   ├── literacy_partners_competitive_positioning.ipynb
│   ├── competitor_pricing_intelligence.py
│   └── market_trends_k8_professional_development.ipynb
│
├── ✉️  03_outreach_automation/           # Personalization at Scale
│   ├── superintendent_research_engine.ipynb        ⭐ OPTION B ADJACENT
│   ├── personalized_email_generator.py
│   ├── linkedin_outreach_optimizer.ipynb
│   └── best_time_to_contact_educators.ipynb
│
├── 🤝 04_sales_cycle_tools/             # Full Cycle Execution
│   ├── discovery_call_prep_dashboard.ipynb
│   ├── proposal_roi_calculator.py
│   ├── objection_handling_playbook.ipynb
│   └── hubspot_pipeline_health_analyzer.ipynb
│
├── 📈 05_case_studies/                  # OPTION B + C: Proof of Concept
│   ├── teacher_to_sales_my_journey.ipynb           ⭐ OPTION C
│   ├── solving_teacher_buy_in_challenge.ipynb      ⭐ OPTION B
│   ├── how_data_science_made_me_top_sdr.ipynb
│   └── k12_sales_is_different_heres_how.ipynb
│
├── 🎯 06_literacy_partners_custom/      # Company-Specific Deep Work
│   ├── why_literacy_partners_analysis.ipynb
│   ├── my_first_90_days_plan.ipynb                 ⭐ BONUS WEAPON
│   └── la_metro_territory_strategy.ipynb
│
├── 🎨 07_streamlit_demo/                # Interactive Live Tools
│   ├── app.py                                       ⭐ DISTRICT DASHBOARD
│   ├── pages/
│   │   ├── 01_district_scorer.py
│   │   ├── 02_superintendent_intel.py
│   │   ├── 03_email_generator.py
│   │   └── 04_pipeline_tracker.py
│   └── requirements.txt
│
├── requirements.txt
├── .env.example
└── README.md                            ← YOU ARE HERE
```

---

## 🏆 The 3 Power Notebooks

### ⭐ Option A: The Nuclear Weapon
**`01_district_intelligence/la_unified_opportunity_analysis.ipynb`**

A complete data-driven analysis of LA Unified — the largest district in California —
identifying a **$2.5M+ opportunity** for Literacy Partners. Built with public CAASPP data,
district budget reports, and decision-maker intelligence.

→ [View on AetherBlog](#) | [Open in Colab](#)

---

### ⭐ Option B: Solving the Real Problem
**`05_case_studies/solving_teacher_buy_in_challenge.ipynb`**

Data-backed analysis of why 68% of district PD pilots fail (teacher resistance),
with a Pilot Readiness Scorecard that helps reps qualify better and close faster.

→ [View on AetherBlog](#) | [Open in Colab](#)

---

### ⭐ Option C: My Story
**`05_case_studies/teacher_to_sales_my_journey.ipynb`**

Honest, data-driven narrative of my transition from K-8 teacher → top-10% SDR,
with the actual tools I built and the metrics they produced.

→ [View on AetherBlog](#) | [Open in Colab](#)

---

## ⚡ Quick Start

```bash
# Clone the repo
git clone https://github.com/[YOUR_USERNAME]/literacy-partners-k8-sales-toolkit.git
cd literacy-partners-k8-sales-toolkit

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Add your API keys (OpenAI, SerpAPI, etc.)

# Launch the Streamlit demo
cd 07_streamlit_demo
streamlit run app.py

# Or open any notebook in Jupyter
jupyter lab
```

---

## 🔑 Environment Variables

Create a `.env` file (copy from `.env.example`):

```
OPENAI_API_KEY=your_key_here
SERPAPI_KEY=your_key_here
HUBSPOT_API_KEY=your_key_here
LINKEDIN_EMAIL=your_email_here
LINKEDIN_PASSWORD=your_password_here
```

> ⚠️ Never commit your `.env` file. It is git-ignored.

---

## 📊 Data Sources Used

| Source | Data | Access |
|--------|------|--------|
| [CAASPP](https://caaspp.cde.ca.gov/) | CA Student Test Scores | Public |
| [EdData.org](https://www.eddata.org) | District Profiles + Budgets | Public |
| [CA Dept of Education](https://www.cde.ca.gov/) | Enrollment, Demographics | Public |
| [USASpending.gov](https://usaspending.gov) | Federal Education Grants | Public |
| [LinkedIn](https://linkedin.com) | Decision Maker Intel | Semi-public |
| [Google News API](https://newsapi.org/) | District News/Initiatives | API Key Required |

---

## 🛠️ Tech Stack

| Layer | Tools |
|-------|-------|
| **Data** | pandas, numpy, requests, BeautifulSoup |
| **ML** | scikit-learn, XGBoost |
| **Visualization** | matplotlib, seaborn, plotly |
| **NLP / AI** | openai, langchain, transformers |
| **Web App** | streamlit, gradio |
| **Automation** | selenium, playwright |
| **CRM** | hubspot-api-client |

---

## 📬 Contact

I built this because I believe in Literacy Partners' mission.
Every child deserves joyful, rigorous, equitable literacy instruction —
and every teacher deserves the tools to deliver it.

I'd love to show you how this toolkit would accelerate your pipeline.

📧 **[your.email@gmail.com]**  
💼 **[LinkedIn Profile URL]**  
🌐 **[AetherBlog Portfolio URL]**

---

*Built with 🍎 (for education) + 🐍 (Python) + ❤️ (for Literacy Partners' mission)*
