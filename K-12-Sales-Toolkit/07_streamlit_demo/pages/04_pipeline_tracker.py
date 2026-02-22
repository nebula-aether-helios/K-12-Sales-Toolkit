import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

try:
    from utils import load_css
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils import load_css

st.set_page_config(page_title="Pipeline Tracker", page_icon="📈", layout="wide")
load_css()

st.header("📈 Pipeline Health Dashboard")
st.markdown("*HubSpot pipeline health metrics*")

# Mock Data
deals = pd.DataFrame({
    "deal_name": [f"Deal {i}" for i in range(20)],
    "amount": [50000, 150000, 250000, 75000, 20000, 300000, 100000, 50000, 40000, 120000] * 2,
    "stage": ["Discovery", "Presentation", "Proposal", "Negotiation", "Closed Won"] * 4,
    "probability": [0.2, 0.4, 0.6, 0.8, 1.0] * 4,
    "days_in_stage": [5, 12, 45, 2, 0, 15, 30, 60, 10, 5] * 2,
    "last_activity_days": [1, 5, 20, 2, 0, 10, 15, 40, 3, 1] * 2
})
deals["weighted_value"] = deals["amount"] * deals["probability"]
deals["risk_flag"] = deals.apply(lambda x: "High Risk" if x["last_activity_days"] > 14 and x["stage"] != "Closed Won" else "Healthy", axis=1)

# Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Pipeline", f"${deals['amount'].sum()/1000:.0f}K")
col2.metric("Weighted Value", f"${deals['weighted_value'].sum()/1000:.0f}K")
col3.metric("Open Deals", len(deals[deals["stage"] != "Closed Won"]))
col4.metric("At Risk", len(deals[deals["risk_flag"] == "High Risk"]))

# Charts
c1, c2 = st.columns(2)
with c1:
    # Aggregated by stage
    funnel_data = deals.groupby("stage").sum(numeric_only=True).reset_index()
    # Sort by order
    stage_order = ["Discovery", "Presentation", "Proposal", "Negotiation", "Closed Won"]
    funnel_data["stage"] = pd.Categorical(funnel_data["stage"], categories=stage_order, ordered=True)
    funnel_data = funnel_data.sort_values("stage")

    fig_funnel = px.funnel(funnel_data, x='amount', y='stage', title="Pipeline Funnel (Value)")
    st.plotly_chart(fig_funnel, use_container_width=True)

with c2:
    fig_risk = px.pie(deals, names='risk_flag', title="Deal Health Risk", color='risk_flag', color_discrete_map={"Healthy": "#048A81", "High Risk": "#C73E1D"})
    st.plotly_chart(fig_risk, use_container_width=True)

st.subheader("⚠️ At Risk Deals (>14 days inactive)")
st.dataframe(deals[deals["risk_flag"] == "High Risk"][["deal_name", "stage", "amount", "last_activity_days"]])
