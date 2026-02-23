"""
app.py — Literacy Partners K-8 Sales Intelligence Dashboard
Interactive Streamlit app demonstrating data-driven sales tools.
"""

import streamlit as st
import pandas as pd
from utils import load_district_data, load_css, COLORS

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="K-8 Sales Intelligence Dashboard",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/[YOUR_USERNAME]/literacy-partners-k8-sales-toolkit",
        "Report a bug": "https://github.com/[YOUR_USERNAME]/literacy-partners-k8-sales-toolkit/issues",
        "About": "Built by [Your Name] for Literacy Partners — Sales Executive Application"
    }
)

load_css()

# ============================================================
# HOME PAGE
# ============================================================

# Header
st.markdown('<div class="main-header">📚 K-8 Sales Intelligence Dashboard</div>',
            unsafe_allow_html=True)
st.markdown('<div class="sub-header">Built for Literacy Partners — By a Former Teacher + SDR + Data Scientist</div>',
            unsafe_allow_html=True)

# Highlight Box
st.markdown("""
<div class="highlight-box">
    <h3 style="color:white; margin:0 0 0.5rem 0">Why this exists</h3>
    <p style="margin:0; font-size:1rem">
    I'm applying for the Sales Executive, K-8 Partnerships role at Literacy Partners.
    Rather than send a resume, I built the tools I'd use on Day 1.
    Every page of this dashboard is a real sales tool — not a demo.
    </p>
</div>
""", unsafe_allow_html=True)

# KPI Row
districts = load_district_data()
col1, col2, col3, col4 = st.columns(4)
with col1:
    t1 = (districts["tier"] == "Tier 1").sum()
    st.metric("🔴 Tier 1 Districts", t1, help="Immediate outreach priority")
with col2:
    t2 = (districts["tier"] == "Tier 2").sum()
    st.metric("🟡 Tier 2 Districts", t2, help="Nurture pipeline")
with col3:
    total_enrollment = districts["enrollment_k8"].sum()
    st.metric("👩‍🎓 Students Reachable", f"{total_enrollment/1e6:.1f}M",
              help="K-8 students in tracked districts")
with col4:
    avg_score = districts["readiness_score"].mean()
    st.metric("📊 Avg Readiness Score", f"{avg_score:.0f}/100",
              help="Average Partnership Readiness Score across all districts")

st.markdown("---")

# Quick Navigation
st.markdown("### 🧭 What Can You Do Here?")
nav_col1, nav_col2 = st.columns(2)

with nav_col1:
    st.markdown("""
    **📊 District Prioritizer** → Rank CA districts by partnership readiness
    **🔬 Superintendent Intel** → Pre-call research in 60 seconds
    **✉️ Email Generator** → 3 personalized email variants per prospect
    """)
with nav_col2:
    st.markdown("""
    **📈 Pipeline Tracker** → HubSpot-connected deal health dashboard
    **🥊 Battle Cards** → Competitive positioning per competitor
    **📅 90-Day Plan** → My first 90 days strategy for Literacy Partners
    """)

st.markdown("---")
st.markdown(
    '<div class="footer-note">Built by [Your Name] | '
    '<a href="https://runforme.app/aetherblog/">AetherBlog Portfolio</a> | '
    '<a href="https://github.com/[YOUR_USERNAME]/literacy-partners-k8-sales-toolkit">GitHub Repo</a>'
    '</div>',
    unsafe_allow_html=True
)

# Sidebar Info
st.sidebar.image("https://literacypartners.com/wp-content/uploads/2021/09/LP-Logo.png",
                 use_column_width=True, caption="Built for Literacy Partners")
st.sidebar.info("👈 Select a tool from the sidebar to get started.")
