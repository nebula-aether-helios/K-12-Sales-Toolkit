
import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime, timedelta

# Import utils from parent if needed
import sys
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
try:
    from utils import load_css, COLORS
except ImportError:
    from ..utils import load_css, COLORS

st.set_page_config(page_title="Pipeline Health", page_icon="📈", layout="wide")
load_css()

# HubSpot API Config (use environment variables)
HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")

def load_deals():
    """
    Loads deal data from HubSpot API (if key present) or generates realistic demo data.
    """
    if HUBSPOT_API_KEY:
        try:
            url = "https://api.hubapi.com/crm/v3/objects/deals?limit=100&properties=dealname,amount,dealstage,closedate,pipeline"
            headers = {
                'Authorization': f'Bearer {HUBSPOT_API_KEY}',
                'Content-Type': 'application/json'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            deals = []
            for item in data.get('results', []):
                props = item['properties']
                deals.append({
                    'deal_name': props.get('dealname'),
                    'amount': float(props.get('amount') or 0),
                    'stage': props.get('dealstage'),
                    'close_date': props.get('closedate'),
                    'id': item['id']
                })

            df = pd.DataFrame(deals)
            # Map raw stage IDs to readable names (simplified mapping)
            stage_map = {
                'appointmentscheduled': 'Discovery',
                'qualifiedtobuy': 'Demo',
                'presentationscheduled': 'Proposal',
                'decisionmakerbought': 'Negotiation',
                'contractsent': 'Contract',
                'closedwon': 'Closed Won',
                'closedlost': 'Closed Lost'
            }
            df['stage_name'] = df['stage'].map(stage_map).fillna('Other')
            df['close_date'] = pd.to_datetime(df['close_date'])
            return df

        except Exception as e:
            st.warning(f"HubSpot connection failed: {e}. Falling back to demo data.")
            return _generate_demo_deals()
    else:
        return _generate_demo_deals()

def _generate_demo_deals():
    """Generates realistic K-12 sales pipeline data."""
    districts = [
        "Los Angeles Unified", "San Diego Unified", "Long Beach Unified",
        "Fresno Unified", "Elk Grove Unified", "San Francisco Unified",
        "Corona-Norco Unified", "Capistrano Unified", "Santa Ana Unified"
    ]

    stages = ["Discovery", "Demo", "Proposal", "Negotiation", "Contract", "Closed Won"]
    weights = [0.3, 0.25, 0.2, 0.1, 0.1, 0.05]

    deals = []
    # Generate 40 active deals
    for _ in range(40):
        district = np.random.choice(districts)
        stage = np.random.choice(stages, p=weights)

        # Amount logic: larger districts -> larger deals
        base_amt = 15000 if "Unified" in district else 5000
        amount = base_amt * np.random.randint(1, 10)

        # Close date: randomized within next 90 days
        days_out = np.random.randint(-30, 90)
        close_date = datetime.now() + timedelta(days=days_out)

        risk = "Healthy"
        if stage in ["Negotiation", "Contract"] and days_out < 0:
            risk = "Stalled"
        elif stage == "Discovery" and days_out > 60:
             risk = "At Risk"

        deals.append({
            "deal_name": f"{district} - K-5 Literacy Pilot",
            "district": district,
            "amount": amount,
            "stage": stage,
            "close_date": close_date,
            "risk_flag": risk
        })

    return pd.DataFrame(deals)

# --- App Layout ---

st.header("📈 Pipeline Health Dashboard")

if not HUBSPOT_API_KEY:
    st.info("ℹ️ Running in Demo Mode. Add `HUBSPOT_API_KEY` to .env to connect live data.")
else:
    st.success("✅ Connected to HubSpot CRM")

deals = load_deals()

# Metrics
col1, col2, col3, col4 = st.columns(4)

total_pipeline = deals[deals['stage'] != 'Closed Lost']['amount'].sum()
weighted_pipeline = 0
stage_probs = {"Discovery": 0.1, "Demo": 0.3, "Proposal": 0.6, "Negotiation": 0.8, "Contract": 0.9, "Closed Won": 1.0}

# Calculate weighted
if 'stage' in deals.columns and 'stage_name' not in deals.columns:
     # Demo data case
     deals['weighted_amount'] = deals.apply(lambda x: x['amount'] * stage_probs.get(x['stage'], 0), axis=1)
elif 'stage_name' in deals.columns:
     # HubSpot data case
     deals['weighted_amount'] = deals.apply(lambda x: x['amount'] * stage_probs.get(x['stage_name'], 0), axis=1)
     # Normalize column name for downstream charts
     deals['stage'] = deals['stage_name']
     deals['risk_flag'] = 'Healthy' # Placeholder for real risk logic

weighted_pipeline = deals['weighted_amount'].sum()

col1.metric("Total Pipeline", f"${total_pipeline/1000:,.1f}K")
col2.metric("Weighted Forecast", f"${weighted_pipeline/1000:,.1f}K")
col3.metric("Open Deals", len(deals))
col4.metric("Avg Deal Size", f"${deals['amount'].mean()/1000:,.1f}K")

# Charts
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("Pipeline by Stage")
    # Aggregate by stage
    stage_order = ["Discovery", "Demo", "Proposal", "Negotiation", "Contract", "Closed Won"]

    stage_df = deals.groupby("stage").agg({"amount": "sum", "deal_name": "count"}).reindex(stage_order).reset_index()

    fig = px.funnel(stage_df, x='amount', y='stage', title="Pipeline Volume by Stage",
                    color_discrete_sequence=[COLORS['primary']])
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("At Risk Deals")
    if 'risk_flag' in deals.columns:
        risky = deals[deals['risk_flag'] != 'Healthy']
        st.dataframe(risky[['deal_name', 'amount', 'risk_flag']], hide_index=True)
    else:
        st.write("No risk analysis available for live data yet.")

# Recent Activity / Deal Table
st.subheader("Recent Deals")
st.dataframe(
    deals.sort_values("close_date").head(10).style.format({"amount": "${:,.0f}", "weighted_amount": "${:,.0f}"}),
    use_container_width=True
)
