import streamlit as st
import pandas as pd
import numpy as np
import os

COLORS = {
    "primary":   "#2E5A88",  # Deep Blue (Brand)
    "secondary": "#048A81",
    "accent":    "#F7941D",  # Orange (Brand)
    "danger":    "#C73E1D",
    "light":     "#F4F4F8",
    "lp_purple": "#5C4B8A",
}

def load_css():
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.2rem;
            font-weight: 800;
            color: #2E5A88;
            margin-bottom: 0.2rem;
        }
        .sub-header {
            font-size: 1.1rem;
            color: #F7941D;
            margin-bottom: 1.5rem;
        }
        .metric-card {
            background: white;
            border-radius: 12px;
            padding: 1.2rem;
            border-left: 4px solid #F7941D;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .tier-1 { background-color: #FFEBEB; border-left: 4px solid #C73E1D; }
        .tier-2 { background-color: #FFF8E1; border-left: 4px solid #F7941D; }
        .tier-3 { background-color: #E8F5E9; border-left: 4px solid #2E5A88; }
        .highlight-box {
            background: linear-gradient(135deg, #2E5A88, #F7941D);
            color: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .footer-note {
            font-size: 0.8rem;
            color: #9E9E9E;
            text-align: center;
            margin-top: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_district_data():
    """Load district data from processed CSVs."""
    # Try different relative paths
    possible_paths = [
        "../data/processed/caaspp_ela_2024.csv", # If running from 07_streamlit_demo
        "K-12-Sales-Toolkit/data/processed/caaspp_ela_2024.csv", # If running from root
        "data/processed/caaspp_ela_2024.csv" # If running from repo root directly
    ]

    data_path = None
    for p in possible_paths:
        if os.path.exists(p):
            data_path = p
            break

    try:
        if data_path:
            df = pd.read_csv(data_path)

            # Aggregate if needed
            if "grade" in df.columns:
                 df = df.groupby("district_name").agg({
                     "percentage_standard_met_and_above": "mean",
                     "students_tested": "sum"
                 }).reset_index()
                 df.rename(columns={
                     "percentage_standard_met_and_above": "pct_ela_proficient",
                     "students_tested": "enrollment_k8"
                 }, inplace=True)

            # Enrich with mock data
            n = len(df)
            np.random.seed(42)
            df["county"] = np.random.choice(["Los Angeles","San Diego","Sacramento","Fresno","Orange"], n)
            df["pct_title1_students"] = np.random.uniform(10, 95, n)
            df["pd_budget_per_student_est"] = np.random.uniform(50, 500, n)
            df["sor_adoption_signal"] = np.random.choice(["None","Exploring","Committed","Implementing"], n, p=[0.3, 0.3, 0.25, 0.15])
            df["recent_literacy_initiative"] = np.random.choice([True, False], n, p=[0.4, 0.6])
            df["superintendent_tenure_yrs"] = np.random.uniform(0.5, 15, n)
            df["teacher_turnover_rate"] = np.random.uniform(5, 45, n)
            df["miles_from_la"] = np.random.uniform(0, 400, n)

            # Score
            def score(row):
                s = 0
                s += max(0, (60 - row["pct_ela_proficient"]) / 60) * 30
                s += min(row["pd_budget_per_student_est"] / 500, 1.0) * 25
                sor_map = {"None": 0, "Exploring": 10, "Committed": 16, "Implementing": 20}
                s += sor_map.get(row["sor_adoption_signal"], 0)
                if row["recent_literacy_initiative"]: s += 8
                if row["superintendent_tenure_yrs"] < 3: s += 7
                s += max(0, (400 - row["miles_from_la"]) / 400) * 10
                return round(s, 1)

            df["readiness_score"] = df.apply(score, axis=1)
            df["tier"] = df["readiness_score"].apply(lambda s: "Tier 1" if s >= 70 else ("Tier 2" if s >= 50 else "Tier 3"))

            return df
        else:
             raise FileNotFoundError("Data processed/caaspp_ela_2024.csv not found")

    except Exception as e:
        print(f"Error loading live data: {e}. Using mock generator.")
        # Fallback (Original Mock)
        np.random.seed(42)
        n = 150
        districts = pd.DataFrame({
            "district_name": [f"District {i:03d}" for i in range(n)],
            "county": np.random.choice(["Los Angeles", "San Diego"], n),
            "enrollment_k8": np.random.randint(500, 80000, n),
            "pct_ela_proficient": np.random.uniform(20, 75, n),
            "pct_title1_students": np.random.uniform(10, 95, n),
            "pd_budget_per_student_est": np.random.uniform(50, 500, n),
            "sor_adoption_signal": np.random.choice(["None", "Exploring", "Committed", "Implementing"], n, p=[0.3, 0.3, 0.25, 0.15]),
            "recent_literacy_initiative": np.random.choice([True, False], n, p=[0.4, 0.6]),
            "superintendent_tenure_yrs": np.random.uniform(0.5, 15, n),
            "teacher_turnover_rate": np.random.uniform(5, 45, n),
            "miles_from_la": np.random.uniform(0, 400, n),
        })
        # Score
        def score(row):
            s = 0
            s += max(0, (60 - row["pct_ela_proficient"]) / 60) * 30
            s += min(row["pd_budget_per_student_est"] / 500, 1.0) * 25
            sor_map = {"None": 0, "Exploring": 10, "Committed": 16, "Implementing": 20}
            s += sor_map.get(row["sor_adoption_signal"], 0)
            if row["recent_literacy_initiative"]: s += 8
            if row["superintendent_tenure_yrs"] < 3: s += 7
            s += max(0, (400 - row["miles_from_la"]) / 400) * 10
            return round(s, 1)

        districts["readiness_score"] = districts.apply(score, axis=1)
        districts["tier"] = districts["readiness_score"].apply(lambda s: "Tier 1" if s >= 70 else ("Tier 2" if s >= 50 else "Tier 3"))
        return districts
