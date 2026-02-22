import streamlit as st
import sys
import os

try:
    from utils import load_css
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils import load_css

st.set_page_config(page_title="Battle Cards", page_icon="🥊", layout="wide")
load_css()

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
