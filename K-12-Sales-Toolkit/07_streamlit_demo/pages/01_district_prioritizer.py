import streamlit as st
import plotly.express as px
import pandas as pd
import sys
import os

# Add parent dir to path to import utils if needed
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
# Also add current dir (repo root) just in case
sys.path.append(os.getcwd())

try:
    from utils import load_district_data, load_css, COLORS
except ImportError:
    # If running from pages/ context, utils might be in parent
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils import load_district_data, load_css, COLORS

st.set_page_config(page_title="District Prioritizer", page_icon="📊", layout="wide")
load_css()

st.header("📊 California District Prioritizer")
st.markdown("*ML-powered account scoring — find your Tier 1 targets instantly*")

districts = load_district_data()

# Filters
st.sidebar.markdown("### 🔽 Filters")
selected_county = st.sidebar.multiselect(
    "County", options=sorted(districts["county"].unique()),
    default=["Los Angeles", "Orange", "Riverside"]
)
min_score = st.sidebar.slider("Min Readiness Score", 0, 100, 50)
sor_filter = st.sidebar.multiselect(
    "SOR Adoption Stage",
    options=["None", "Exploring", "Committed", "Implementing"],
    default=["Committed", "Implementing"]
)

# Filter
filtered = districts[
    (districts["county"].isin(selected_county) if selected_county else True) &
    (districts["readiness_score"] >= min_score) &
    (districts["sor_adoption_signal"].isin(sor_filter) if sor_filter else True)
].sort_values("readiness_score", ascending=False)

# Metrics
c1, c2, c3 = st.columns(3)
c1.metric("Districts Found", len(filtered))
c2.metric("Tier 1 Targets", (filtered["tier"] == "Tier 1").sum())
c3.metric("Avg Score", f"{filtered['readiness_score'].mean():.0f}")

# Scatter Plot
fig = px.scatter(
    filtered,
    x="pct_ela_proficient",
    y="pd_budget_per_student_est",
    color="tier",
    size="enrollment_k8",
    hover_name="district_name",
    hover_data={"readiness_score": True, "sor_adoption_signal": True,
                "county": True},
    color_discrete_map={"Tier 1": COLORS["danger"], "Tier 2": COLORS["accent"],
                         "Tier 3": COLORS["secondary"]},
    title="District Prioritization Matrix: Need vs. Budget",
    labels={"pct_ela_proficient": "ELA Proficiency % (lower = higher need)",
            "pd_budget_per_student_est": "PD Budget per Student ($)"},
)
fig.update_layout(height=450)
st.plotly_chart(fig, use_container_width=True)

# Table
st.markdown("### 🎯 Priority List")
display_cols = ["district_name", "county", "readiness_score", "tier",
                "pct_ela_proficient", "sor_adoption_signal", "enrollment_k8"]
st.dataframe(
    filtered[display_cols].head(30).reset_index(drop=True),
    use_container_width=True,
    height=400,
)

# Export
csv = filtered[display_cols].to_csv(index=False)
st.download_button(
    "⬇️ Download Priority List (CSV)",
    data=csv,
    file_name="tier1_district_targets.csv",
    mime="text/csv",
)
