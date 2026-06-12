import streamlit as st
import pandas as pd
import os, base64
from data_manager import (register_authority, login_authority, get_all_complaints,
                           get_all_workers, update_complaint, add_blockchain_entry,
                           verify_blockchain, get_management_complaints, drone_patrol_and_escalate, now_iso)

st.set_page_config(page_title="Civic Solvers — Authority", page_icon="🏛️", layout="wide")

# On EVERY load of Authority dashboard, run drone patrol
patrol_result = drone_patrol_and_escalate()

session = st.session_state.get("authority_session")

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
if session:
    auth_name = session.get("username", "Authority")
    dept = session.get("department", "")
    city = session.get("city", "")
    st.sidebar.success(f"**Logged In:** {auth_name}")
    st.sidebar.info(f"**City:** {city} | **Dept:** {dept}")
    if patrol_result["violations_found"] > 0:
        st.sidebar.warning(f"🚁 Drone patrol found {patrol_result['violations_found']} violation(s) — management complaints filed automatically.")
    if st.sidebar.button("Logout"):
        del st.session_state["authority_session"]
        st.rerun()

# ── NOT LOGGED IN ─────────────────────────────────────────────────────────────
if not session:
    st.title("🏛️ Authority Command Center")
    tab_login, tab_reg = st.tabs(["🔐 Log In", "📝 Register Authority Account"])
    
    with tab_login:
        st.subheader("Login to Authority Command Center")
        with st.form("login_auth_form"):
            user = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Unlock Dashboard", type="primary")
            
        if login_btn:
            result = login_authority(user.strip(), password)
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state["authority_session"] = result
                st.success(f"✅ Access granted. Welcome, {result.get('username')}!")
                st.rerun()
                
    with tab_reg:
        st.subheader("Register Authority Account")
        with st.form("register_auth_form"):
            user_r = st.text_input("Username *")
            password_r = st.text_input("Password *", type="password")
            dept_r = st.selectbox("Department Jurisdiction *",
                                  ["Roads & Infrastructure Dept",
                                   "Water Supply & Sewerage Board",
                                   "Electrical & Lighting Dept",
                                   "Stormwater Drainage Dept",
                                   "Solid Waste Management Dept",
                                   "Horticulture & Parks Dept",
                                   "Town Planning & Development",
                                   "General Administration"])
            city_r = st.text_input("City Jurisdiction *")
            submitted = st.form_submit_button("Create Account", type="primary")
            
        if submitted:
            if not all([user_r, password_r, city_r]):
                st.error("All fields are required.")
            else:
                result = register_authority(user_r.strip(), password_r, dept_r, city_r.strip())
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state["authority_session"] = result
                    st.success(f"✅ Account created. Welcome {user_r}!")
                    st.rerun()
    st.stop()

# ── LOGGED IN ─────────────────────────────────────────────────────────────────
session = st.session_state["authority_session"]
authority_name = session.get("username", "Authority")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Live Dashboard", "📁 Issue Management", "🗺️ Geospatial Heatmap", 
    "🚁 Drone Escalations", "👷 Worker Directories", "🔗 Blockchain Audits", "📈 Analytics"
])

complaints = get_all_complaints()

# ── TAB 1: LIVE DASHBOARD ─────────────────────────────────────────────────────
with tab1:
    st.subheader("Executive Summary")
    
    total = len(complaints)
    active = len([c for c in complaints if c.get("status") not in ("CLOSED", "VERIFIED_COMPLETE", "CITIZEN_RATED")])
    resolved = len([c for c in complaints if c.get("status") in ("CLOSED", "VERIFIED_COMPLETE", "CITIZEN_RATED")])
    critical = len([c for c in complaints if c.get("priority") == "CRITICAL" and c.get("status") not in ("CLOSED", "VERIFIED_COMPLETE", "CITIZEN_RATED")])
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Complaints", total)
    col2.metric("Active Cases", active)
    col3.metric("Resolved Cases", resolved)
    col4.metric("Active Critical Cases", critical)

# ── TAB 2: ISSUE MANAGEMENT ───────────────────────────────────────────────────
with tab2:
    st.subheader("Service Desk Assignments")
    
    if not complaints:
        st.info("No complaints registered yet.")
    else:
        for c in complaints:
            cid = c.get("complaint_id", "")
            status = c.get("status", "")
            priority = c.get("priority", "MEDIUM")
            
            with st.expander(f"📋 {cid} — {c.get('issue_type','')} | Status: {status} | Priority: {priority}"):
                st.write(f"**Citizen:** {c.get('citizen_name','')} | **Location:** {c.get('location_text','')}")
                st.write(f"**Description:** {c.get('description','')}")
                
                # Show before photo
                photo_b64 = c.get("photo_b64", "")
                if photo_b64:
                    try:
                        img_bytes = base64.b64decode(photo_b64)
                        st.image(img_bytes, caption="Before photo by citizen", width=300)
                    except Exception:
                        st.caption("📷 Photo stored securely.")
                
                # Show completion photo if exists
                comp_photo_b64 = c.get("completion_photo_b64", "")
                if comp_photo_b64:
                    try:
                        img_bytes_c = base64.b64decode(comp_photo_b64)
                        st.image(img_bytes_c, caption="After photo by worker", width=300)
                    except Exception:
                        st.caption("📷 Completion photo stored.")
                        
                # Assign worker
                if status in ("ASSIGNED", "PENDING", "REQUIRES_REWORK"):
                    workers = get_all_workers()
                    if workers:
                        worker_options = {f"{w['name']} (ID: {w['worker_id']}) ⭐{w.get('avg_rating',0):.1f}": w['worker_id']
                                         for w in workers}
                        selected_worker_label = st.selectbox("Assign Worker", list(worker_options.keys()), key=f"sel_{cid}")
                        selected_worker_id = worker_options[selected_worker_label]
                        if st.button("Assign Worker", key=f"btn_assign_{cid}", type="primary"):
                            update_complaint(cid, {
                                "assigned_worker_id": selected_worker_id,
                                "status": "ASSIGNED",
                                "assigned_at": now_iso(),
                            }, f"Assigned to worker {selected_worker_id}", authority_name)
                            add_blockchain_entry(cid, "ASSIGNED", authority_name)
                            st.success("✅ Worker assigned.")
                            st.rerun()
                    else:
                        st.warning("No workers registered yet.")
                else:
                    st.write(f"**Assigned Worker:** {c.get('assigned_worker_id')}")

# ── TAB 3: GEOSPATIAL HEATMAP ─────────────────────────────────────────────────
with tab3:
    st.subheader("City GIS Hotspot Map")
    import folium
    from streamlit_folium import st_folium
    
    m = folium.Map(location=[20.9250, 77.7660], zoom_start=10)
    for c in complaints:
        lat, lng = c.get("latitude"), c.get("longitude")
        if lat and lng:
            folium.Marker(
                [lat, lng],
                popup=f"CS-{c.get('complaint_id')}: {c.get('issue_type')}",
                tooltip=c.get("issue_type")
            ).add_to(m)
    st_folium(m, height=400, use_container_width=True)

# ── TAB 4: DRONE ESCALATIONS ──────────────────────────────────────────────────
with tab4:
    st.subheader("🚁 Autonomous Drone Operations")

    # Show patrol status
    st.success("🟢 Drone Patrol System: ACTIVE — Scanning automatically on every dashboard load")

    # Show all management complaints filed by drone
    mgmt_complaints = get_management_complaints()
    if not mgmt_complaints:
        st.info("✅ No violations detected yet. Drone patrol running clean.")
        st.markdown("""
        **Drone Autonomous Functions:**
        - ✅ Scans for workers who haven't accepted jobs within 24 hours
        - ✅ Detects SLA breaches and escalates automatically  
        - ✅ Verifies completion photos after worker upload
        - ✅ Files management complaints with zero human input
        """)
    else:
        st.error(f"🚨 {len(mgmt_complaints)} violation(s) detected by drone")
        for mc in mgmt_complaints:
            with st.expander(f"MC: {mc.get('management_complaint_id')} — {mc.get('violation')}"):
                st.write(f"**Complaint:** {mc.get('complaint_id')}")
                st.write(f"**Worker:** {mc.get('worker_id')}")
                st.write(f"**Violation:** {mc.get('violation')}")
                st.write(f"**Evidence:** {mc.get('note')}")
                st.write(f"**Filed by:** {mc.get('filed_by')} at {mc.get('filed_at','')[:16]}")
                status = mc.get('status','OPEN')
                if status == 'OPEN':
                    col1, col2 = st.columns(2)
                    if col1.button("Issue Warning", key=f"warn_{mc.get('management_complaint_id')}"):
                        # Update database lock-safe
                        from data_manager import _load, _save, _lock
                        with _lock:
                            db = _load()
                            wid = mc.get("worker_id")
                            if wid in db["workers"]:
                                db["workers"][wid]["penalty_count"] = db["workers"][wid].get("penalty_count", 0) + 1
                            mc_id = mc.get("management_complaint_id")
                            if mc_id in db["management_complaints"]:
                                db["management_complaints"][mc_id]["status"] = "REVIEWED"
                                db["management_complaints"][mc_id]["action"] = "Warning issued"
                            _save(db)
                        st.success("Warning issued to worker.")
                        st.rerun()
                    if col2.button("Reassign Complaint", key=f"reassign_{mc.get('management_complaint_id')}"):
                        update_complaint(mc.get("complaint_id"), {
                            "status": "PENDING",
                            "assigned_worker_id": None,
                            "assigned_at": None,
                            "accepted_at": None
                        }, "Authority reassigned task.", authority_name)
                        from data_manager import _load, _save, _lock
                        with _lock:
                            db = _load()
                            mc_id = mc.get("management_complaint_id")
                            if mc_id in db["management_complaints"]:
                                db["management_complaints"][mc_id]["status"] = "ACTIONED"
                                db["management_complaints"][mc_id]["action"] = "Reassigned"
                            _save(db)
                        st.success("Complaint reassigned.")
                        st.rerun()

# ── TAB 5: WORKER DIRECTORY ───────────────────────────────────────────────────
with tab5:
    st.subheader("Registered Field Contractors")
    workers = get_all_workers()
    if not workers:
        st.info("No workers registered yet.")
    else:
        df_w = pd.DataFrame(workers)
        st.dataframe(df_w[["worker_id", "name", "city", "avg_rating", "completed_jobs", "performance_flag"]], use_container_width=True)

# ── TAB 6: BLOCKCHAIN AUDITS ──────────────────────────────────────────────────
with tab6:
    st.subheader("Immutable Blockchain Ledger Audit")
    
    if st.button("Run Full Cryptographic Verification", type="primary"):
        report = verify_blockchain()
        if report.get("intact", False):
            st.success(report.get("message"))
        else:
            st.error(report.get("message"))
            
    from data_manager import _load
    db = _load()
    chain = db.get("blockchain", [])
    if not chain:
        st.info("Blockchain is empty.")
    else:
        df_c = pd.DataFrame(chain)
        st.dataframe(df_c[["timestamp", "complaint_id", "event", "actor", "photo_hash", "prev_hash"]], use_container_width=True)

# ── TAB 7: ANALYTICS ──────────────────────────────────────────────────────────
with tab7:
    st.subheader("Fiscal & Analytical Overview")
    if not complaints:
        st.info("No data to plot.")
    else:
        df = pd.DataFrame(complaints)
        st.write("**Complaint Status Breakdown:**")
        st.bar_chart(df["status"].value_counts())
        st.write("**Complaint Issue Type Breakdown:**")
        st.bar_chart(df["issue_type"].value_counts())
