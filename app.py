"""
app.py — Civic Solvers main entry point.
Bootstraps GCP infrastructure, configures multi-page Streamlit navigation.

Problem: Manual, unverified civic reporting causes 15-day delays and erodes public trust.
         India: 1.5 crore civic complaints/year | 30% resolution rate | 12,000+ pothole deaths
Solution: AI analysis in <30 seconds | Blockchain fraud prevention | Autonomous drone verification
"""
import streamlit as st
from setup import bootstrap_gcp

st.set_page_config(
    page_title="Civic Solvers",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Run idempotent GCP bootstrap on every cold start
@st.cache_resource
def init_gcp():
    bootstrap_gcp()
    try:
        from scripts.gcp_seed import seed_db
        seed_db()
    except Exception as e:
        print(f"⚠️ Database seeding skipped/failed: {e}")
    return True

init_gcp()

# Session state initialization
if "citizen_session" not in st.session_state:
    st.session_state.citizen_session = None
if "worker_session" not in st.session_state:
    st.session_state.worker_session = None
if "authority_session" not in st.session_state:
    st.session_state.authority_session = False

# Main landing page
st.title("🏙️ Civic Solvers")
st.subheader("Smarter Cities. Faster Fixes. Transparent Governance.")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("National Complaint Resolution", "30%", delta="Target: 90%+", delta_color="normal")
with col2:
    st.metric("AI Analysis Speed", "<30 seconds", delta="vs 15-day delays", delta_color="normal")
with col3:
    st.metric("Annual Damage Potential", "₹50,000 Crore", delta="Savings via early resolution", delta_color="normal")

st.markdown("---")
st.markdown("""
### How Civic Solvers Works

**Citizens** upload a photo → AI analyzes in <30 seconds → Authority gets auto-prioritized alert → Worker dispatched → Drone verifies completion → Citizen rates work → System learns.

**Only 3 human actions required.** Everything else is fully autonomous.

Navigate using the sidebar to access:
- 🧑‍💼 **Citizen Portal** — Report issues, track complaints, earn civic points
- 👷 **Worker Portal** — View assigned jobs, upload completion proof
- 🏛️ **Authority Dashboard** — Command center, analytics, blockchain audit
""")

st.sidebar.markdown("## 🏙️ Civic Solvers")
st.sidebar.markdown("**Team:** Obsidian Ops / Indic Intelligence")
st.sidebar.markdown("**Lead:** Shreyas Patankar")
st.sidebar.markdown("**Institutes:** PRMITR & PRMCEM")
st.sidebar.markdown("---")
st.sidebar.markdown("*PU Code Hackathon 3.0 + AWS AI for Bharat*")
