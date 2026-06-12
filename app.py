import streamlit as st
import os

os.makedirs("data", exist_ok=True)

st.set_page_config(
    page_title="Civic Solvers",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.markdown("## 🏙️ Civic Solvers")
st.sidebar.markdown("*Smarter Cities. Faster Fixes. Transparent Governance.*")
st.sidebar.markdown("---")

st.title("🏙️ Civic Solvers")
st.subheader("Smarter Cities. Faster Fixes. Transparent Governance.")

col1, col2, col3 = st.columns(3)
col1.metric("National Complaint Resolution", "30%", delta="Our Target: 90%+")
col2.metric("AI Analysis Speed", "<30 seconds", delta="vs 15-day delays")
col3.metric("Annual Damage Potential", "₹50,000 Crore", delta="Savings via early resolution")

st.markdown("---")
st.markdown("""
### How Civic Solvers Works

**Only 3 human actions. Everything else is fully autonomous.**

1. 🧑💼 **Citizen** creates account → uploads photo → submits complaint
2. 👷 **Worker** creates account → accepts assigned job → uploads completion proof
3. 🏛️ **Authority** creates account → views dashboard → assigns workers

**AI handles automatically:**
- Photo analysis and fake detection
- Risk scoring and priority assignment
- Repair plan and budget calculation
- Blockchain recording of every event
- Drone verification of completed work
- Gamification points awarded
- Management complaints for SLA breaches

Use the sidebar to navigate.
""")
