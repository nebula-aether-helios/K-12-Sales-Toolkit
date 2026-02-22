import streamlit as st
import sys
import os

# Add src to path
# Repo root should be in path if running streamlit from there
sys.path.append(os.getcwd())
# Also try adding K-12-Sales-Toolkit/src explicitly
sys.path.append(os.path.join(os.getcwd(), 'K-12-Sales-Toolkit', 'src'))
# And just src
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from researcher import SuperintendentResearcher
except ImportError:
    st.error("Could not load researcher module. Please check path configuration.")
    class SuperintendentResearcher:
        def research(self, n, d): return {}

try:
    from utils import load_css
except ImportError:
    # Try importing from parent
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils import load_css

st.set_page_config(page_title="Superintendent Intel", page_icon="🔬", layout="wide")
load_css()

st.header("🔬 Superintendent Intelligence Tool")
st.markdown("*Automated deep-dive research on district decision makers*")

with st.form("research_form"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Contact Name", placeholder="e.g. Dr. Michelle King")
    with col2:
        district = st.text_input("District", placeholder="e.g. Los Angeles Unified")
    submitted = st.form_submit_button("🔍 Research")

if submitted and name and district:
    with st.spinner(f"Researching {name} at {district}..."):
        researcher = SuperintendentResearcher()
        profile = researcher.research(name, district)

        brief = profile.get("ai_brief", {})

        st.success("Research Complete!")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader(f"Strategy Brief: {name}")
            st.info(f"**Best Angle:** {brief.get('best_angle')}")

            st.markdown("### 🛑 Top Pain Points")
            for p in brief.get('pain_points', []):
                st.markdown(f"- {p}")

            st.markdown("### 🗣️ Talking Points")
            for t in brief.get('talking_points', []):
                st.markdown(f"- {t}")

        with col2:
            st.subheader("Context")
            st.markdown(f"**District:** {district}")
            st.markdown(f"**Data:** {profile.get('district_data')}")
            st.markdown("**Recent News:**")
            for n in profile.get('news_mentions', []):
                st.markdown(f"- {n}")

            with st.expander("LinkedIn Bio (Simulated)"):
                st.write(profile.get('linkedin'))

        st.download_button(
            "⬇️ Download Brief",
            data=str(brief),
            file_name=f"brief_{name.replace(' ', '_')}.txt",
        )
