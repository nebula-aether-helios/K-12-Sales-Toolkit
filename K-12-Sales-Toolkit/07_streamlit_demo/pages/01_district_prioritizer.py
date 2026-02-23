
import streamlit as st
import plotly.express as px
import pandas as pd
import sys
import os

# Add parent dir to path to import utils if needed
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
sys.path.append(os.getcwd())

# Add src to path for CLV model
_nb_dir = os.path.dirname(os.path.abspath(__file__))
_repo_root = os.path.abspath(os.path.join(_nb_dir, '..', '..'))
sys.path.insert(0, os.path.join(_repo_root, 'src'))

try:
    from utils import load_district_data, load_css, COLORS
    from clv_model import compute_clv
except ImportError:
    # Fallback for different CWDs
    try:
        from ...utils import load_district_data, load_css, COLORS
        from ...src.clv_model import compute_clv
    except ImportError:
        # Last resort: mock imports to prevent crash if paths are totally wrong
        st.error("Could not import required modules. Check sys.path.")
        st.stop()

st.set_page_config(page_title="District Prioritizer", page_icon="📊", layout="wide")
load_css()

st.header("📊 California District Prioritizer")
st.markdown("*ML-powered account scoring — find your Tier 1 targets instantly*")

# Load Data
@st.cache_data
def get_data_with_clv():
    df = load_district_data()
    # Apply CLV model
    df = compute_clv(df)
    return df

districts = get_data_with_clv()

# Sidebar Filters
st.sidebar.markdown("### 🔽 Filters")

# County Filter
all_counties = sorted(districts["county"].dropna().unique().tolist())
default_counties = ["Los Angeles", "Orange", "San Diego"]
selected_county = st.sidebar.multiselect(
    "County", options=all_counties,
    default=[c for c in default_counties if c in all_counties]
)

# Score Filter
min_score = st.sidebar.slider("Min Readiness Score", 0, 100, 50)

# CLV Tier Filter (New!)
clv_tiers = ["Platinum", "Gold", "Silver"]
selected_tiers = st.sidebar.multiselect(
    "CLV Tier (Projected Value)",
    options=clv_tiers,
    default=["Platinum", "Gold"]
)

# Apply Filters
mask = (districts["readiness_score"] >= min_score)
if selected_county:
    mask &= districts["county"].isin(selected_county)
if selected_tiers:
    mask &= districts["clv_tier"].isin(selected_tiers)

filtered = districts[mask].sort_values("readiness_score", ascending=False)

# Top Metrics Row
c1, c2, c3, c4 = st.columns(4)
c1.metric("Districts Found", len(filtered))
c2.metric("Tier 1 Targets", (filtered["tier"] == "Tier 1").sum())

# CLV Metrics
avg_clv = filtered['predicted_value_3yr'].mean()
total_opportunity = filtered['predicted_value_3yr'].sum()

c3.metric("Avg 3-Year CLV", f"${avg_clv:,.0f}")
c4.metric("Total Opportunity", f"${total_opportunity/1000000:.1f}M")


# Main Visualization: Value vs. Readiness
st.subheader("District Value Matrix")
st.markdown("Identifies high-value targets (Y-axis) that are ready to buy (X-axis).")

fig = px.scatter(
    filtered,
    x="readiness_score",
    y="predicted_value_3yr",
    color="clv_tier",
    size="enrollment_k8",
    hover_name="district_name",
    hover_data={
        "county": True,
        "churn_prob": ":.1%",
        "predicted_purchases_3yr": ":.1f"
    },
    color_discrete_map={
        "Platinum": COLORS["primary"],
        "Gold": COLORS["accent"],
        "Silver": "grey"
    },
    title="Readiness Score vs. Projected Lifetime Value",
    labels={
        "readiness_score": "Pilot Readiness Score (0-100)",
        "predicted_value_3yr": "Projected 3-Year CLV ($)"
    }
)
fig.update_layout(height=500)
st.plotly_chart(fig, use_container_width=True)

# Detailed Data Table
st.markdown("### 🎯 Priority Target List")

display_cols = [
    "district_name", "county", "readiness_score", "clv_tier",
    "predicted_value_3yr", "churn_prob", "enrollment_k8"
]

st.dataframe(
    filtered[display_cols].style.format({
        "predicted_value_3yr": "${:,.0f}",
        "churn_prob": "{:.1%}",
        "readiness_score": "{:.0f}"
    }),
    use_container_width=True,
    height=400
)

# Export
csv = filtered[display_cols].to_csv(index=False)
st.download_button(
    "⬇️ Download Priority List (CSV)",
    data=csv,
    file_name="tier1_clv_targets.csv",
    mime="text/csv",
)
