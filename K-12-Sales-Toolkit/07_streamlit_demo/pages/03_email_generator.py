import streamlit as st
import sys
import os

try:
    from utils import load_css
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils import load_css

st.set_page_config(page_title="Email Generator", page_icon="✉️", layout="wide")
load_css()

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
