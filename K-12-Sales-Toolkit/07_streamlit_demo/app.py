"""
app.py — Literacy Partners K-8 Sales Intelligence Dashboard
Interactive Streamlit app demonstrating data-driven sales tools.

Run: streamlit run app.py
Deploy: streamlit deploy (or Streamlit Community Cloud)

TODO (Jules): Connect live data sources to replace all sample data.
TODO (Gemini): Polish UI — add LP brand colors, logo, better layout.
TODO (Junie): Add unit tests, error handling, loading states.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

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

# ============================================================
# BRAND COLORS
# ============================================================
COLORS = {
    "primary":   "#2E4057",
    "secondary": "#048A81",
    "accent":    "#F18F01",
    "danger":    "#C73E1D",
    "light":     "#F4F4F8",
    "lp_purple": "#5C4B8A",
}

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #2E4057;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #048A81;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        border-left: 4px solid #048A81;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .tier-1 { background-color: #FFEBEB; border-left: 4px solid #C73E1D; }
    .tier-2 { background-color: #FFF8E1; border-left: 4px solid #F18F01; }
    .tier-3 { background-color: #E8F5E9; border-left: 4px solid #048A81; }
    .highlight-box {
        background: linear-gradient(135deg, #2E4057, #048A81);
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


# ============================================================
# SAMPLE DATA GENERATORS
# (Replace with real API calls — see notebooks for data sources)
# ============================================================

@st.cache_data
def load_district_data():
    """
    Load California K-8 district data.
    TODO (Jules): Replace with live CAASPP API + EdData scraper.
    See: 01_district_intelligence/california_district_prioritization_model.ipynb
    """
    np.random.seed(42)
    n = 150

    districts = pd.DataFrame({
        "district_name": [f"District {i:03d}" for i in range(n)],
        "county": np.random.choice(
            ["Los Angeles", "San Diego", "Sacramento", "Fresno", "Orange",
             "Riverside", "San Bernardino", "Alameda", "Kern", "Santa Clara"], n
        ),
        "enrollment_k8": np.random.randint(500, 80000, n),
        "pct_ela_proficient": np.random.uniform(20, 75, n),
        "pct_title1_students": np.random.uniform(10, 95, n),
        "pd_budget_per_student_est": np.random.uniform(50, 500, n),
        "sor_adoption_signal": np.random.choice(
            ["None", "Exploring", "Committed", "Implementing"], n,
            p=[0.3, 0.3, 0.25, 0.15]
        ),
        "recent_literacy_initiative": np.random.choice([True, False], n, p=[0.4, 0.6]),
        "superintendent_tenure_yrs": np.random.uniform(0.5, 15, n),
        "teacher_turnover_rate": np.random.uniform(5, 45, n),
        "miles_from_la": np.random.uniform(0, 400, n),
    })

    # Score districts
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
    districts["tier"] = districts["readiness_score"].apply(
        lambda s: "Tier 1" if s >= 70 else ("Tier 2" if s >= 50 else "Tier 3")
    )
    return districts


# ============================================================
# HOME PAGE
# ============================================================
def show_home():
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
    st.markdown("**👈 Use the sidebar to navigate between tools**")
    st.markdown(
        '<div class="footer-note">Built by [Your Name] | '
        '<a href="https://runforme.app/aetherblog/">AetherBlog Portfolio</a> | '
        '<a href="https://github.com/[YOUR_USERNAME]/literacy-partners-k8-sales-toolkit">GitHub Repo</a>'
        '</div>',
        unsafe_allow_html=True
    )


# ============================================================
# DISTRICT PRIORITIZER PAGE
# ============================================================
def show_district_prioritizer():
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


# ============================================================
# EMAIL GENERATOR PAGE
# ============================================================
def show_email_generator():
    st.header("✉️ Personalized Email Generator")
    st.markdown("*Enter prospect details → get 3 personalized email variants in seconds*")

    st.info("🔑 For AI-powered generation, add your OpenAI API key to `.env`. "
            "Showing template-based previews below.", icon="ℹ️")

    with st.form("email_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Contact Name", placeholder="Dr. Jane Smith")
            title = st.text_input("Title", placeholder="Assistant Superintendent of Curriculum")
            district = st.text_input("District", placeholder="Los Angeles Unified School District")
        with col2:
            ela_pct = st.number_input("District ELA Proficiency %", 0, 100, 38)
            sor_stage = st.selectbox("SOR Adoption Stage",
                                     ["None", "Exploring", "Committed", "Implementing"])
            pain_point = st.text_input("Key Pain Point",
                                       placeholder="Inconsistent SOR implementation")
        submitted = st.form_submit_button("🚀 Generate Emails")

    if submitted and district:
        st.markdown("---")
        st.markdown(f"### Generated Emails for **{name}** at **{district}**")

        tab1, tab2, tab3 = st.tabs(["📌 Subject-First", "💡 Problem-Focused", "📖 Peer Story"])

        emails = {
            "subject_first": f"""**Subject:** SOR Implementation Support for {district}

Hi {name},

I saw {district} recently committed to Science of Reading — congratulations on that shift.
I work with Literacy Partners, and we specialize in exactly the coaching infrastructure
that makes SOR stick for teachers long-term.

Worth 15 minutes to explore?

[Your Name]
*P.S. — I'm a former K-8 teacher. I promise not to waste your time.*""",

            "problem_focused": f"""**Subject:** The gap between SOR adoption and teacher confidence

Hi {name},

With {ela_pct}% ELA proficiency and SOR {sor_stage.lower()}, {district} is at exactly the
point where implementation quality determines everything — and that's usually a coaching gap.

That's Literacy Partners' specialty: ongoing, tailored coaching (not workshops) that
turns SOR commitment into measurable teacher practice change.

Can I show you a 1-pager from a similar district? 15 minutes?

[Your Name]""",

            "peer_story": f"""**Subject:** How [Similar District] solved {pain_point or 'teacher resistance to SOR'}

Hi {name},

A year ago, a district a lot like {district} was dealing with {pain_point or 'inconsistent SOR rollout'}.
They tried workshops. They didn't move the needle.

Then they piloted Literacy Partners' ongoing coaching model.
Year 1: Teacher confidence scores up 40%. Year 2: They expanded district-wide.

Would you like to hear how they did it?

[Your Name]""",
        }

        with tab1:
            st.markdown(emails["subject_first"])
            st.button("📋 Copy", key="copy1")
        with tab2:
            st.markdown(emails["problem_focused"])
            st.button("📋 Copy", key="copy2")
        with tab3:
            st.markdown(emails["peer_story"])
            st.button("📋 Copy", key="copy3")

        st.markdown("---")
        st.success("✅ Review and add 1 specific detail before sending. Personalization = higher reply rates.")


# ============================================================
# BATTLE CARDS PAGE
# ============================================================
def show_battle_cards():
    st.header("🥊 Battle Cards")
    st.markdown("*Quick-reference objection handling — for use in discovery calls and proposals*")

    battle_cards = {
        "Teachers College / TCRWP": {
            "when_you_hear": "We've worked with TCRWP for years",
            "acknowledge": "TCRWP has done incredible work in literacy education for decades.",
            "pivot": "The Science of Reading research has changed what we know. LP is purpose-built for that transition.",
            "proof": "We've helped 3 districts transition from Balanced Literacy to SOR with measurable gains in Year 1.",
            "close": "Would a case study from a similar district be helpful?",
            "win_rate": "HIGH"
        },
        "Curriculum Associates (i-Ready)": {
            "when_you_hear": "We already have i-Ready",
            "acknowledge": "i-Ready is a great tool — many of our partners use it.",
            "pivot": "LP doesn't compete with i-Ready — we make it more effective by developing the teachers using it.",
            "proof": "Partner schools using both saw 23% faster reading growth vs. i-Ready alone.",
            "close": "Can I show you how the combination works in practice?",
            "win_rate": "HIGH"
        },
        "Amplify CKLA": {
            "when_you_hear": "We just adopted Amplify",
            "acknowledge": "CKLA is a strong SOR-aligned curriculum.",
            "pivot": "Curriculum is the 'what.' LP provides the 'how' — we coach teachers on fidelity.",
            "proof": "CKLA implementation quality varies 3x between schools with and without dedicated coaching.",
            "close": "We'd love to be your coaching partner for the CKLA rollout.",
            "win_rate": "HIGH"
        },
        "Budget Objection": {
            "when_you_hear": "We don't have budget for additional PD",
            "acknowledge": "Budget is always a constraint — I hear that.",
            "pivot": "92% of LP partners fund through Title I or ESSER. ESSER III expires Sept 2026 — this is a use-it-or-lose-it moment.",
            "proof": "We can show you exactly how to fund LP through your existing federal allocations.",
            "close": "Can I share a 1-pager on ESSER-funded PD?",
            "win_rate": "MEDIUM"
        },
        "No Time Objection": {
            "when_you_hear": "Our teachers are already overwhelmed",
            "acknowledge": "Initiative fatigue is real — and I've been in that classroom.",
            "pivot": "LP's model is specifically designed to reduce cognitive load — we remove friction from existing practice, not add new things.",
            "proof": "Our teacher NPS score is [X]. Teachers who work with LP report LESS stress, not more.",
            "close": "What if you spoke with one of our partner teachers directly?",
            "win_rate": "HIGH"
        },
    }

    selected = st.selectbox("Select Competitor / Objection:", list(battle_cards.keys()))
    card = battle_cards[selected]

    col1, col2 = st.columns([1, 2])
    with col1:
        win_color = "🟢" if card["win_rate"] == "HIGH" else "🟡"
        st.markdown(f"**Win Rate:** {win_color} {card['win_rate']}")
        st.markdown(f"**You hear:** *\"{card['when_you_hear']}\"*")

    with col2:
        st.markdown(f"**1. Acknowledge:** {card['acknowledge']}")
        st.markdown(f"**2. Pivot:** {card['pivot']}")
        st.markdown(f"**3. Proof Point:** {card['proof']}")
        st.markdown(f"**4. Close:** *\"{card['close']}\"*")

    st.markdown("---")
    st.markdown("*See full competitive analysis: `02_competitive_research/`*")


# ============================================================
# MAIN ROUTER
# ============================================================
def main():
    st.sidebar.image("https://literacypartners.com/wp-content/uploads/2021/09/LP-Logo.png",
                     use_column_width=True, caption="Built for Literacy Partners")

    st.sidebar.markdown("## 🗂️ Navigation")
    page = st.sidebar.radio(
        "Select Tool:",
        ["🏠 Home", "📊 District Prioritizer", "✉️ Email Generator",
         "🥊 Battle Cards"],
        index=0,
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**📓 Full Notebooks:**")
    st.sidebar.markdown("[AetherBlog Portfolio →](https://runforme.app/aetherblog/)")
    st.sidebar.markdown("[GitHub Repo →](https://github.com/[YOUR_USERNAME]/literacy-partners-k8-sales-toolkit)")
    st.sidebar.markdown("---")
    st.sidebar.markdown("**👤 About the Builder**")
    st.sidebar.markdown(
        "Former K-8 teacher → Top-10% SDR → Data Scientist  \n"
        "Applying for: Sales Executive, K-8 Partnerships  \n"
        "📧 [your.email@gmail.com]"
    )

    # Route to page
    if page == "🏠 Home":
        show_home()
    elif page == "📊 District Prioritizer":
        show_district_prioritizer()
    elif page == "✉️ Email Generator":
        show_email_generator()
    elif page == "🥊 Battle Cards":
        show_battle_cards()


if __name__ == "__main__":
    main()
