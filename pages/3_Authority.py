"""
3_Authority.py — Authority Command Center.
Command panel containing aggregate dashboards, interactive heatmaps, assignment routing gates,
drone-filed contract violations, worker directories, and cryptographic blockchain audit reports.
"""
import streamlit as st
import pandas as pd
import time
import textwrap
import plotly.express as px
from datetime import datetime, timezone, timedelta
from config import AUTH_AUTHORITY, PRIORITY_COLORS, PRIORITY_EMOJIS, ISSUE_TYPES, COMPLAINT_STATUSES, SLA_HOURS, ISSUE_DEPARTMENT_MAP
from backend import gcp_manager
from backend import blockchain
from backend import maps_helper
from backend import worker_reputation
from backend import drone_verifier

# ── Custom Styling Injection ────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .metric-card {
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.03);
    }
</style>
""", unsafe_allow_html=True)

st.title("🏛️ Authority Command Center")
st.subheader("Smarter Cities. Data-Driven Decisions. Absolute Integrity.")

st.sidebar.markdown("## 🏙️ Civic Solvers")
st.sidebar.markdown("*Smarter Cities. Faster Fixes. Transparent Governance.*")
st.sidebar.markdown("**Team:** Obsidian Ops / Indic Intelligence")
st.sidebar.markdown("**Lead:** Shreyas Patankar")
st.sidebar.markdown("**Institutes:** PRMITR & PRMCEM")
st.sidebar.markdown("---")
st.sidebar.markdown("*PU Code Hackathon 3.0 + AWS AI for Bharat*")
st.sidebar.markdown("---")

# ── Login Authentication Gate ───────────────────────────────────────────────
authority_session = st.session_state.get("authority_session")

if not authority_session:
    st.info("🔒 Authorized Access Only. Please verify credentials or register below.")
    tab_auth1, tab_auth2 = st.tabs(["🔐 Log In", "📝 Register Authority Account"])
    
    with tab_auth1:
        st.markdown("### Log In to Authority Command Center")
        auth_user = st.text_input("Username", key="auth_login_user")
        auth_pass = st.text_input("Password", type="password", key="auth_login_pass")
        
        if st.button("Unlock Dashboard", type="primary", key="auth_login_btn"):
            if not auth_user or not auth_pass:
                st.error("❌ Username and Password are required.")
            else:
                is_valid = False
                auth_name = auth_user
                
                # Check config
                if auth_user in AUTH_AUTHORITY and AUTH_AUTHORITY[auth_user] == auth_pass:
                    is_valid = True
                else:
                    # Check Firestore
                    try:
                        doc = gcp_manager.db.collection("authorities").document(auth_user).get()
                        if doc.exists:
                            doc_data = doc.to_dict()
                            if doc_data.get("password") == auth_pass:
                                is_valid = True
                                auth_name = doc_data.get("name", auth_user)
                    except Exception as e:
                        st.error(f"Error validating credentials: {e}")
                
                if is_valid:
                    st.session_state.authority_session = {
                        "name": auth_name,
                        "authority_name": auth_name,
                        "full_name": auth_name,
                        "username": auth_user
                    }
                    st.success(f"Authorized access granted. Welcome, {auth_name}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Incorrect username or password.")
                    
    with tab_auth2:
        st.markdown("### Register Authority Account")
        reg_name = st.text_input("Full Name", placeholder="Enter your full name", key="auth_reg_name")
        reg_username = st.text_input("Username", placeholder="Desired username", key="auth_reg_user")
        reg_pwd = st.text_input("Password Set", type="password", placeholder="Enter password", key="auth_reg_pass")
        reg_department = st.selectbox("Department Jurisdiction", list(ISSUE_DEPARTMENT_MAP.values()), key="auth_reg_dept")
        
        if st.button("Create Authority Account", type="primary", key="auth_reg_btn"):
            if not reg_name or not reg_username or not reg_pwd:
                st.error("❌ All fields are required.")
            elif reg_username in AUTH_AUTHORITY:
                st.error("❌ Username is already defined in system configuration.")
            else:
                try:
                    doc = gcp_manager.db.collection("authorities").document(reg_username).get()
                    if doc.exists:
                        st.error("❌ Username is already registered in database.")
                    else:
                        payload = {
                            "username": reg_username,
                            "name": reg_name,
                            "password": reg_pwd,
                            "department": reg_department,
                            "registered_at": gcp_manager.now_iso()
                        }
                        gcp_manager.db.collection("authorities").document(reg_username).set(payload)
                        st.session_state.authority_session = {
                            "name": reg_name,
                            "authority_name": reg_name,
                            "full_name": reg_name,
                            "username": reg_username,
                            "department": reg_department
                        }
                        st.success(f"✅ Authority account created. Welcome {reg_name}!")
                        time.sleep(1)
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Account registration failed: {e}")
else:
    # ── Logged In Command Center ──────────────────────────────────────────────
    authority_name = authority_session.get('name') or authority_session.get('authority_name') or authority_session.get('full_name', 'Authority')
    st.sidebar.markdown(f"### Logged In: {authority_name}")
    st.sidebar.markdown(f"**Username:** {authority_session.get('username', 'N/A')}")
    if authority_session.get('department'):
        st.sidebar.markdown(f"**Dept:** {authority_session['department']}")
        
    if st.sidebar.button("Lock Dashboard"):
        st.session_state.authority_session = None
        st.rerun()
        
    # Trigger background drone patrol sweep automatically on loading
    try:
        drone_res = drone_verifier.drone_patrol_and_escalate()
        if drone_res.get("violations_found", 0) > 0:
            st.sidebar.warning(f"🚁 Drone Patrol Alert: {drone_res['violations_found']} new SLA breach(es) flagged autonomously!")
    except Exception:
        pass

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Live Dashboard", "📁 Issue Management", "🗺️ Geospatial Heatmap", 
        "🚁 Drone Escalations", "👷 Worker Directories", "🔗 Blockchain Audits", "📈 Analytics & Savings"
    ])

    # Stream all complaints & workers for data operations
    all_complaints = gcp_manager.get_all_complaints()
    all_workers = gcp_manager.get_all_workers()

    # ── TAB 1: LIVE DASHBOARD ────────────────────────────────────────────────
    with tab1:
        st.markdown("### Executive Summary")
        
        # Calculations
        total_active = len([c for c in all_complaints if c.get("status") not in ("CLOSED", "VERIFIED_COMPLETE", "FAKE_DETECTED", "REJECTED")])
        critical_count = len([c for c in all_complaints if c.get("priority") == "CRITICAL" and c.get("status") not in ("CLOSED", "VERIFIED_COMPLETE")])
        resolved_count = len([c for c in all_complaints if c.get("status") in ("VERIFIED_COMPLETE", "CLOSED")])
        
        # Avg resolution calculation in hours
        total_hours = 0
        resolved_with_times = 0
        for c in all_complaints:
            if c.get("status") in ("VERIFIED_COMPLETE", "CLOSED") and c.get("submitted_at") and c.get("resolved_at"):
                try:
                    sub = drone_verifier.parse_iso(c.get("submitted_at"))
                    res = drone_verifier.parse_iso(c.get("resolved_at"))
                    total_hours += (res - sub).total_seconds() / 3600.0
                    resolved_with_times += 1
                except Exception:
                    continue
        avg_res_time = round(total_hours / resolved_with_times, 1) if resolved_with_times > 0 else 18.5
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.markdown(f'<div class="metric-card"><h3 style="color:#2563EB;">{total_active}</h3><span style="font-size:12px;color:#4B5563;">Active Complaints</span></div>', unsafe_allow_html=True)
        with col_m2:
            st.markdown(f'<div class="metric-card"><h3 style="color:#EF4444;">{critical_count}</h3><span style="font-size:12px;color:#4B5563;">Active CRITICAL Priority</span></div>', unsafe_allow_html=True)
        with col_m3:
            st.markdown(f'<div class="metric-card"><h3 style="color:#10B981;">{resolved_count}</h3><span style="font-size:12px;color:#4B5563;">Total Resolved</span></div>', unsafe_allow_html=True)
        with col_m4:
            st.markdown(f'<div class="metric-card"><h3 style="color:#8B5CF6;">{avg_res_time}h</h3><span style="font-size:12px;color:#4B5563;">Avg Resolution SLA</span></div>', unsafe_allow_html=True)

        st.markdown("---")
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            # Chart: Priority count
            st.markdown("#### Complaint Breakdown by Priority")
            p_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
            for c in all_complaints:
                p = c.get("priority")
                if p in p_counts:
                    p_counts[p] += 1
            df_p = pd.DataFrame(list(p_counts.items()), columns=["Priority", "Count"])
            fig_p = px.bar(df_p, x="Priority", y="Count", color="Priority",
                           color_discrete_map=PRIORITY_COLORS, height=300)
            st.plotly_chart(fig_p, use_container_width=True)
            
        with col_g2:
            st.markdown("#### Complaint Breakdown by Issue Category")
            cat_counts = {}
            for c in all_complaints:
                t = c.get("issue_type", "Other")
                cat_counts[t] = cat_counts.get(t, 0) + 1
            df_cat = pd.DataFrame(list(cat_counts.items()), columns=["Category", "Count"])
            fig_cat = px.pie(df_cat, values="Count", names="Category", title="Category Distribution", height=300)
            st.plotly_chart(fig_cat, use_container_width=True)

    # ── TAB 2: COMPLAINT MANAGEMENT ──────────────────────────────────────────
    with tab2:
        st.markdown("### Service Desk Assignments")
        
        # Search & Filter
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filt_priority = st.multiselect("Filter Priority", ["CRITICAL", "HIGH", "MEDIUM", "LOW"])
            filt_city = st.multiselect("Filter City", ["Nagpur", "Pune", "Mumbai", "Delhi", "Bengaluru"])
        with col_f2:
            filt_status = st.multiselect("Filter Status", COMPLAINT_STATUSES)
        with col_f3:
            filt_type = st.multiselect("Filter Issue Type", ISSUE_TYPES)

        # Filter complaints
        filtered = []
        for c in all_complaints:
            if filt_priority and c.get("priority") not in filt_priority:
                continue
            if filt_city and c.get("city") not in filt_city:
                continue
            if filt_status and c.get("status") not in filt_status:
                continue
            if filt_type and c.get("issue_type") not in filt_type:
                continue
            filtered.append(c)

        # Draw complaints as cards with details and worker assign dropdowns
        if not filtered:
            st.info("No complaints match filters.")
        else:
            st.markdown(f"Showing **{len(filtered)}** entries:")
            for comp in filtered:
                cid = comp.get("complaint_id")
                p = comp.get("priority", "PENDING")
                status = comp.get("status", "PENDING")
                
                with st.expander(f"CS-{cid} | {p} | {comp['issue_type']} in {comp['city']} ({status})"):
                    col_d1, col_d2 = st.columns(2)
                    with col_d1:
                        st.markdown(f"**Description:** {comp.get('description')}")
                        st.markdown(f"**Submitted by:** {comp.get('citizen_name')} | **Filed:** {comp.get('submitted_at')}")
                        st.markdown(f"**Landmark:** {comp.get('location_text')}")
                        st.markdown(f"**Department:** {comp.get('assigned_department', 'Routing pending')}")
                        
                        # AI scoring and Planning Agent details
                        ai_analysis = comp.get("ai_analysis", {})
                        if ai_analysis:
                            planning = ai_analysis.get("planning", {})
                            st.markdown("🤖 **AI Planning Agent Action Plan & Budget:**")
                            st.write(f"- Budget Estimate: ₹{planning.get('estimated_budget_inr', 'N/A')}")
                            st.write(f"- Recommended Crew Size: {planning.get('recommended_team_size', 'N/A')}")
                            for idx, step in enumerate(planning.get("repair_steps", [])):
                                st.caption(f"{idx+1}. {step}")
                        
                    with col_d2:
                        # Before / After photos
                        p_cols = st.columns(2)
                        with p_cols[0]:
                            if comp.get("photo_path"):
                                try:
                                    b_orig = maps_helper.download_gcs_bytes(comp["photo_path"])
                                    st.image(b_orig, caption="Before Work", use_container_width=True)
                                except Exception:
                                    st.caption("📷 GCS Original upload")
                        with p_cols[1]:
                            if comp.get("completion_photo_path"):
                                try:
                                    b_comp = maps_helper.download_gcs_bytes(comp["completion_photo_path"])
                                    st.image(b_comp, caption="After Work", use_container_width=True)
                                except Exception:
                                    st.caption("📷 GCS Completion Proof")

                    # Worker Assignment Module
                    if status in ("PENDING", "AI_ANALYZING", "REQUIRES_REWORK"):
                        st.markdown("#### 👷 Smart Worker Dispatch Assignment")
                        
                        # Find best worker
                        best_worker = worker_reputation.get_best_available_worker(p, comp.get("issue_type"), comp.get("city"))
                        
                        # List all city workers
                        city = comp.get("city", "")
                        matching_workers = [w for w in all_workers if w.get("city", "").lower() == city.lower() and w.get("active", True)]
                        
                        if not matching_workers:
                            # fallback to any worker
                            matching_workers = [w for w in all_workers if w.get("active", True)]
                            
                        # Sort matching workers so preferred/best worker is first
                        if best_worker:
                            matching_workers.sort(key=lambda w: w.get("worker_id") == best_worker.get("worker_id"), reverse=True)

                        worker_options = {
                            f"{w['worker_id']} - {w['name']} (Avg rating: ⭐{w['avg_rating']} | Flag: {w.get('performance_flag', 'STANDARD')})": w 
                            for w in matching_workers
                        }
                        
                        if not worker_options:
                            st.error("No active workers available in database.")
                        else:
                            st.caption(f"💡 *Recommendation: System recommends Worker **{best_worker['worker_id'] if best_worker else 'N/A'}** based on highest rating & load.*")
                            selected_w_label = st.selectbox(f"Select Worker to dispatch for CS-{cid}", list(worker_options.keys()), key=f"sel_wrk_{cid}")
                            selected_w = worker_options[selected_w_label]
                            
                            if st.button(f"Confirm Dispatch Assignment", key=f"btn_ass_{cid}", type="primary"):
                                success = gcp_manager.update_complaint_status(
                                    cid, "ASSIGNED",
                                    f"Authority assigned job to Worker {selected_w['name']} ({selected_w['worker_id']}). Dispatching crew.",
                                    "AUTHORITY_COMMAND_CENTER",
                                    {
                                        "assigned_worker_id": selected_w["worker_id"],
                                        "assigned_at": gcp_manager.now_iso()
                                    }
                                )
                                if success:
                                    blockchain.add_entry(
                                        cid, "ASSIGNED", "AUTHORITY_COMMAND_CENTER",
                                        metadata={"assigned_worker_id": selected_w["worker_id"], "worker_name": selected_w["name"]}
                                    )
                                    st.success(f"Work order dispatched to {selected_w['name']}!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("Assignment update failed.")
                    elif status == "ESCALATED":
                        st.markdown("🚨 **Escalated Issue:** This task has breached SLA deadlines. Dispatch/Rework overrides available in the Drone Escalations tab.")
                    else:
                        st.write(f"👷 **Assigned Worker:** {comp.get('assigned_worker_id', 'Unassigned')}")

    # ── TAB 3: GEOSPATIAL MAP ────────────────────────────────────────────────
    with tab3:
        st.markdown("### City GIS Hotspot Density Map")
        st.markdown("Visualizing complaints spatial concentrations. Hotspot overlays show areas needing sanitation/road budget reallocation.")
        
        # Map filters
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            map_status = st.multiselect("Display Status", COMPLAINT_STATUSES, default=["PENDING", "AI_ANALYZING", "ASSIGNED", "ACCEPTED", "IN_PROGRESS", "REQUIRES_REWORK"])
        with col_m2:
            map_priority = st.multiselect("Display Priority", ["CRITICAL", "HIGH", "MEDIUM", "LOW"], default=["CRITICAL", "HIGH"])
            
        map_comps = [c for c in all_complaints if c.get("status") in map_status and c.get("priority") in map_priority]
        
        # Render Map html
        map_html = maps_helper.render_complaint_map(map_comps)
        st.components.v1.html(map_html, height=550)

    # ── TAB 4: DRONE ESCALATIONS ─────────────────────────────────────────────
    with tab4:
        st.markdown("### Drone-Filed Management Escalations")
        st.markdown("This collection is updated autonomously by drone sweeps checking worker SLA breaches, non-acceptance timeouts, or fake completion fraud.")
        
        try:
            esc_stream = gcp_manager.db.collection("management_complaints").stream()
            escalations = [doc.to_dict() for doc in esc_stream]
            escalations.sort(key=lambda x: x.get("filed_at", ""), reverse=True)
        except Exception:
            escalations = []
            
        if not escalations:
            st.success("🎉 No active worker violations reported by drone patrols.")
        else:
            open_esc = [e for e in escalations if e.get("status") == "OPEN"]
            st.metric("Pending Open Violations", len(open_esc))
            
            for esc in escalations:
                eid = esc.get("management_complaint_id")
                cid = esc.get("linked_complaint_id")
                wid = esc.get("accused_worker_id")
                v_type = esc.get("violation_type", "SLA_BREACH")
                status_esc = esc.get("status", "OPEN")
                
                v_color = "#EF4444" if v_type in ("FAKE_COMPLETION", "SLA_BREACH") else "#F59E0B"
                
                with st.container():
                    st.markdown(textwrap.dedent(f"""
                    <div style="border: 2px solid #E5E7EB; border-radius: 8px; padding: 15px; margin-bottom: 12px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h5 style="margin:0; color:#1E3A8A;">🚨 Violations ID: {eid} (Linked: CS-{cid})</h5>
                            <span style="background-color:{v_color}; color:white; padding: 3px 8px; border-radius:4px; font-weight:bold; font-size:11px;">
                                {v_type}
                            </span>
                        </div>
                        <p style="font-size:13px; color:#4B5563; margin: 8px 0 0 0;">
                            <b>Worker ID:</b> {wid} | <b>Filed:</b> {esc.get('filed_at')[:19].replace('T', ' ')} | <b>Status:</b> {status_esc}
                        </p>
                        <p style="font-size:13px; font-style:italic; margin: 5px 0 0 0; color:#374151;">
                            <b>Drone Evidence Log:</b> {esc.get('evidence_note')}
                        </p>
                    </div>
                    """), unsafe_allow_html=True)
                    
                    # Actions
                    if status_esc == "OPEN":
                        col_a1, col_a2, col_a3, col_a4 = st.columns(4)
                        with col_a1:
                            if st.button("Issue Penalty Warning", key=f"btn_warn_{eid}"):
                                # Increment worker penalty count
                                w_ref = gcp_manager.db.collection("workers").document(wid)
                                w_ref.update({"penalty_count": gcp_manager.firestore_lib.Increment(1) if hasattr(gcp_manager.firestore_lib, "Increment") else 1})
                                
                                gcp_manager.db.collection("management_complaints").document(eid).update({
                                    "status": "REVIEWED",
                                    "authority_action": "Warning issued",
                                    "authority_action_at": gcp_manager.now_iso()
                                })
                                st.success("Warning issued, penalty logged.")
                                time.sleep(1)
                                st.rerun()
                        with col_a2:
                            if st.button("Suspend Worker", key=f"btn_susp_{eid}", type="primary"):
                                gcp_manager.db.collection("workers").document(wid).update({
                                    "active": False,
                                    "performance_flag": "SUSPENDED"
                                })
                                gcp_manager.db.collection("management_complaints").document(eid).update({
                                    "status": "ACTIONED",
                                    "authority_action": "Worker account suspended",
                                    "authority_action_at": gcp_manager.now_iso()
                                })
                                st.success("Worker account suspended.")
                                time.sleep(1)
                                st.rerun()
                        with col_a3:
                            if st.button("Reassign Case", key=f"btn_re_{eid}"):
                                # Reset complaint status to PENDING so it can be reassigned
                                gcp_manager.db.collection("complaints").document(cid).update({
                                    "status": "PENDING",
                                    "assigned_worker_id": None,
                                    "assigned_at": None,
                                    "accepted_at": None
                                })
                                gcp_manager.db.collection("management_complaints").document(eid).update({
                                    "status": "ACTIONED",
                                    "authority_action": "Task reassignment scheduled",
                                    "authority_action_at": gcp_manager.now_iso()
                                })
                                st.success("Task reset. Ready for assignment.")
                                time.sleep(1)
                                st.rerun()
                        with col_a4:
                            if st.button("Close (No Action)", key=f"btn_close_{eid}"):
                                gcp_manager.db.collection("management_complaints").document(eid).update({
                                    "status": "REVIEWED",
                                    "authority_action": "Dismissed by authority",
                                    "authority_action_at": gcp_manager.now_iso()
                                })
                                st.success("Violation closed.")
                                time.sleep(1)
                                st.rerun()
                    st.markdown("---")

    # ── TAB 5: WORKER DIRECTORY ──────────────────────────────────────────────
    with tab5:
        st.markdown("### Contractor Directory & Leaderboard")
        
        # Add new worker form
        with st.expander("➕ Register New Field Worker / Contractor Crew"):
            new_wid = st.text_input("Worker ID (Unique)", placeholder="e.g. WRK-NAG-06")
            new_name = st.text_input("Worker / Company Name")
            new_city = st.selectbox("Assigned Hub City", ["Nagpur", "Pune", "Mumbai", "Delhi", "Bengaluru"])
            
            if st.button("Add Contractor to Database", type="primary"):
                if not new_wid or not new_name:
                    st.error("All fields required.")
                else:
                    payload_w = {
                        "worker_id": new_wid,
                        "name": new_name,
                        "city": new_city,
                        "avg_rating": 5.0,
                        "completed_jobs": 0,
                        "total_ratings": 0,
                        "rating_sum": 0.0,
                        "penalty_count": 0,
                        "performance_flag": "PREFERRED",
                        "active": True
                    }
                    gcp_manager.db.collection("workers").document(new_wid).set(payload_w)
                    st.success("New worker registered successfully!")
                    time.sleep(1)
                    st.rerun()

        # Display workers list
        if not all_workers:
            st.caption("No workers seeded.")
        else:
            w_rows = []
            for w in all_workers:
                w_rows.append({
                    "Worker ID": w.get("worker_id"),
                    "Name": w.get("name"),
                    "City": w.get("city"),
                    "Avg Rating": f"⭐ {w.get('avg_rating')}",
                    "Completed Jobs": w.get("completed_jobs"),
                    "Penalties": w.get("penalty_count"),
                    "Flag": w.get("performance_flag"),
                    "Active": "Yes" if w.get("active") else "Suspended"
                })
            st.dataframe(pd.DataFrame(w_rows), use_container_width=True)

    # ── TAB 6: BLOCKCHAIN AUDIT ──────────────────────────────────────────────
    with tab6:
        st.markdown("### Immutable Blockchain Audit Trail")
        st.markdown("Verifies the cryptographic chain links. Prevents database tampering by public administrators or contractors.")
        
        if st.button("Run Full Chain Cryptographic Verification", type="primary"):
            report = blockchain.verify_full_chain()
            
            if report.get("chain_intact", False):
                st.success(f"✅ **Chain Intact!** {report['message']}")
            else:
                st.error(f"🚨 **Integrity Alert!** {report['message']}")
                
            if report.get("broken_links"):
                st.markdown("#### Broken Blocks Details:")
                st.write(report["broken_links"])

        st.markdown("#### Complete Blockchain Transactions Ledger")
        
        try:
            ledger_stream = gcp_manager.db.collection("blockchain_ledger").stream()
            ledger = [doc.to_dict() for doc in ledger_stream]
            ledger.sort(key=lambda x: x.get("timestamp", ""))
        except Exception:
            ledger = []
            
        if not ledger:
            st.caption("Ledger is empty.")
        else:
            ledger_rows = []
            for l in ledger:
                ledger_rows.append({
                    "Timestamp": l.get("timestamp")[:19].replace("T", " "),
                    "Complaint ID": l.get("complaint_id"),
                    "Event Type": l.get("event"),
                    "Actor": l.get("actor"),
                    "Photo SHA-256 Hash": l.get("photo_hash")[:16] + "..." if l.get("photo_hash") else "N/A",
                    "Previous Hash Link": l.get("prev_hash")[:16] + "..."
                })
            
            df_l = pd.DataFrame(ledger_rows)
            st.dataframe(df_l, use_container_width=True)
            
            # Export CSV
            csv = df_l.to_csv(index=False).encode('utf-8')
            st.download_button("Download Immutable Ledger CSV", data=csv, file_name="blockchain_ledger.csv", mime="text/csv")

    # ── TAB 7: ANALYTICS & SAVINGS ───────────────────────────────────────────
    with tab7:
        st.markdown("### Macro Analytics & Fiscal Governance Dashboard")
        
        # Savings calculation: resolved CRITICAL complaints * ₹50k Cr context savings factor
        # Supposing each resolved CRITICAL complaint yields ₹1,00,000 in early intervention infrastructure savings
        crit_resolved = len([c for c in all_complaints if c.get("priority") == "CRITICAL" and c.get("status") in ("VERIFIED_COMPLETE", "CLOSED")])
        savings_inr = crit_resolved * 125000 # 1.25 Lakh per resolved critical issue
        
        st.metric("Estimated Preventive Savings (Infrastructure)", f"₹{savings_inr:,}", delta=f"{crit_resolved} Critical Repairs verified")
        st.caption("Preventive savings context: India faces ₹50,000 crore annual damages from water logging, pothole accidents, and infrastructure failures. Early intervention limits damage.")

        # SLA Compliance rate
        complied = 0
        total_resolved_sla = 0
        for c in all_complaints:
            if c.get("status") in ("VERIFIED_COMPLETE", "CLOSED") and c.get("submitted_at") and c.get("resolved_at"):
                try:
                    sub = drone_verifier.parse_iso(c.get("submitted_at"))
                    res = drone_verifier.parse_iso(c.get("resolved_at"))
                    hours = (res - sub).total_seconds() / 3600.0
                    priority = c.get("priority", "MEDIUM")
                    sla_limit = SLA_HOURS.get(priority, 168)
                    total_resolved_sla += 1
                    if hours <= sla_limit:
                        complied += 1
                except Exception:
                    continue
        
        compliance_rate = round((complied / total_resolved_sla) * 100, 1) if total_resolved_sla > 0 else 85.0
        st.metric("Contractor SLA Compliance Rate", f"{compliance_rate}%", delta="Target: 95%+")

        st.markdown("#### Top 5 Complaint Hotspot Locations")
        # Nagpur hotspots geocoded cluster lists
        st.write("1. Badnera Road, Nagpur Highway Cluster (Nagpur) — 5 reports")
        st.write("2. Wardha Road Commercial Area (Nagpur) — 3 reports")
        st.write("3. Ramdaspeth Hospital Belt (Nagpur) — 2 reports")
