# Data Directory

## Structure
- `raw/` — Raw data files (not committed to git — large files)
- `processed/` — Cleaned, processed datasets ready for analysis
- `exports/` — CSV exports for HubSpot import

## Data Sources

| Dataset | Source | File | Notes |
|---------|--------|------|-------|
| CA ELA Proficiency | [CAASPP](https://caaspp.cde.ca.gov/) | `processed/caaspp_ela_2024.csv` | Public |
| District Profiles | [EdData.org](https://www.eddata.org) | `processed/ca_districts.csv` | Public |
| ESSER Grants | [USASpending.gov](https://usaspending.gov) | `processed/esser_grants_ca.csv` | Public |
| LAUSD Budget | [LAUSD Budget Portal](https://achieve.lausd.net/budget) | `raw/lausd_budget_2025.pdf` | Public |

## How to Populate

Run the data collection notebooks in order:
1. `01_district_intelligence/california_district_prioritization_model.ipynb`
2. `01_district_intelligence/la_unified_opportunity_analysis.ipynb`

Or run: `python scripts/fetch_all_data.py` (TODO: build this)
