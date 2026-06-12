import streamlit as st
import os, base64
from data_manager import (register_worker, login_worker, get_worker_jobs,
                           update_complaint, add_blockchain_entry, hash_bytes, now_iso)

st.set_page_config(page_title="Civic Solvers — Worker", page_icon="👷", layout="wide")

session = st.session_state.get("worker_session")

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
if session:
    worker_name = session.get("name", "Worker")
    worker_id = session.get("worker_id", "")
    city = session.get("city", "")
    st.sidebar.success(f"**Logged In:** {worker_name}")
    st.sidebar.info(f"**Worker ID:** {worker_id} | **Hub City:** {city}")
    if st.sidebar.button("Logout"):
        del st.session_state["worker_session"]
        st.rerun()

# ── NOT LOGGED IN ─────────────────────────────────────────────────────────────
if not session:
    st.title("👷 Worker Portal")
    tab_reg, tab_login = st.tabs(["📝 Register Worker Account", "🔐 Log In"])
    
    with tab_reg:
        st.subheader("Create Your Worker / Contractor Account")
        with st.form("register_worker_form"):
            name = st.text_input("Name / Company Name *")
            w_id = st.text_input("Worker ID * (Unique)")
            password = st.text_input("Password *", type="password")
            city = st.text_input("Assigned Hub City *")
            skills = st.multiselect("Skills / Certifications *",
                                    ["Pothole", "Water Leak", "Broken Streetlight", "Blocked Drain",
                                     "Garbage Dump", "Road Damage", "Fallen Tree", "Illegal Construction",
                                     "Sewage Overflow", "Other"])
            submitted = st.form_submit_button("Register", type="primary")
        
        if submitted:
            if not all([name, w_id, password, city, skills]):
                st.error("All fields are required.")
            else:
                result = register_worker(name.strip(), w_id.strip(), password,
                                         city.strip(), skills)
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state["worker_session"] = result
                    st.success(f"✅ Welcome {name}! Account registered successfully.")
                    st.rerun()
                    
    with tab_login:
        st.subheader("Login to Worker Portal")
        with st.form("login_worker_form"):
            w_id_l = st.text_input("Worker ID")
            password_l = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Unlock Job Queue", type="primary")
            
        if login_btn:
            result = login_worker(w_id_l.strip(), password_l)
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state["worker_session"] = result
                st.success(f"✅ Welcome back, {result.get('name')}!")
                st.rerun()
    st.stop()

# ── LOGGED IN ─────────────────────────────────────────────────────────────────
session = st.session_state["worker_session"]
worker_id = session.get("worker_id", "")
worker_name = session.get("name", "Worker")

tab1, tab2, tab3 = st.tabs(["📋 My Job Queue", "📤 Upload Repair Proof", "📈 My Rating Performance"])

# ── TAB 1: JOB QUEUE ──────────────────────────────────────────────────────────
with tab1:
    st.subheader("Your Assigned Tasks")
    jobs = get_worker_jobs(worker_id)
    
    if not jobs:
        st.info("No jobs assigned yet.")
    else:
        for job in jobs:
            cid = job.get("complaint_id", "")
            status = job.get("status", "")
            priority = job.get("priority", "MEDIUM")
            
            with st.expander(f"📋 Job ID: {cid} | Priority: {priority} ({status})"):
                st.write(f"**Issue:** {job.get('issue_type', '')}")
                st.write(f"**Description:** {job.get('description', '')}")
                st.write(f"**Location:** {job.get('location_text', '')}")
                st.write(f"**ETA Deadline:** {job.get('resolution_eta', '')}")
                
                # Show before photo
                photo_b64 = job.get("photo_b64", "")
                if photo_b64:
                    try:
                        img_bytes = base64.b64decode(photo_b64)
                        st.image(img_bytes, caption="Before photo by citizen", width=300)
                    except Exception:
                        st.caption("📷 Photo stored securely.")
                else:
                    st.caption("📷 No photo attached.")
                
                # Planning details
                ai_analysis = job.get("ai_analysis", {})
                planning = ai_analysis.get("planning", {})
                if planning:
                    st.write("**Recommended Plan:**")
                    st.write(f"- Budget: ₹{planning.get('budget_inr', 0):,}")
                    st.write(f"- Team Size: {planning.get('team_size', 0)} workers")
                    for step in planning.get("steps", []):
                        st.caption(step)
                
                # Actions
                if status == "ASSIGNED":
                    if st.button("Confirm Accept Job", key=f"accept_{cid}", type="primary"):
                        update_complaint(cid, {
                            "status": "ACCEPTED",
                            "accepted_at": now_iso()
                        }, "Worker accepted job assignment. Preparing tools.", worker_name)
                        add_blockchain_entry(cid, "ACCEPTED", worker_name)
                        st.success("Job accepted!")
                        st.rerun()
                elif status == "ACCEPTED":
                    if st.button("Mark Work: IN PROGRESS", key=f"start_{cid}"):
                        update_complaint(cid, {
                            "status": "IN_PROGRESS",
                            "work_started_at": now_iso()
                        }, "Worker arrived on-site. Excavation/repair started.", worker_name)
                        add_blockchain_entry(cid, "WORK_STARTED", worker_name)
                        st.success("Work marked in progress!")
                        st.rerun()

# ── TAB 2: UPLOAD PROOF ───────────────────────────────────────────────────────
with tab2:
    st.subheader("Upload Completion Proof")
    uploadable_jobs = [j for j in get_worker_jobs(worker_id) if j.get("status") in ("ACCEPTED", "IN_PROGRESS", "REQUIRES_REWORK")]
    
    if not uploadable_jobs:
        st.info("No active tasks in progress. You must accept and start a job first.")
    else:
        selected_cid = st.selectbox("Select Active Job ID", [j["complaint_id"] for j in uploadable_jobs])
        selected_job = next(j for j in uploadable_jobs if j["complaint_id"] == selected_cid)
        
        # Display before photo
        photo_b64 = selected_job.get("photo_b64", "")
        if photo_b64:
            try:
                img_bytes = base64.b64decode(photo_b64)
                st.image(img_bytes, caption="Before photo by citizen", width=300)
            except Exception:
                st.caption("📷 Photo stored securely.")
        else:
            st.caption("📷 No photo attached.")
            
        completion_file = st.file_uploader("Upload Completion Photo *", type=["jpg","jpeg","png"])
        if completion_file and st.button("Submit Proof — Trigger Drone Scan"):
            completion_bytes = completion_file.read()
            import base64
            completion_b64 = base64.b64encode(completion_bytes).decode()
            completion_hash = hash_bytes(completion_bytes)
            
            update_complaint(selected_cid, {
                "completion_photo_b64": completion_b64,
                "completion_photo_hash": completion_hash,
                "status": "DRONE_SCANNING",
                "completion_uploaded_at": now_iso(),
            }, "Worker uploaded completion proof. Drone scan initiated.", worker_name)
            
            add_blockchain_entry(selected_cid, "COMPLETION_UPLOADED", worker_name, completion_hash)
            
            # Trigger drone verification autonomously
            with st.spinner("🚁 Drone scanning before/after..."):
                from ai_engine import run_drone_verify
                original_b64 = selected_job.get("photo_b64", "")
                verdict = run_drone_verify(selected_cid, original_b64, completion_b64)
            
            st.success(f"✅ Drone scan complete: **{verdict['verdict']}** ({verdict['completion_percentage']}%)")
            st.info(verdict['notes'])
            st.rerun()

# ── TAB 3: PERFORMANCE ────────────────────────────────────────────────────────
with tab3:
    st.subheader("Your Reputation Dashboard")
    from data_manager import _load
    db = _load()
    w_data = db["workers"].get(worker_id, session)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Average Rating", f"⭐ {w_data.get('avg_rating', 0.0):.2f}")
    col2.metric("Completed Jobs", w_data.get("completed_jobs", 0))
    col3.metric("Status Flag", w_data.get("performance_flag", "STANDARD"))
    
    if w_data.get("performance_flag") == "REVIEW_REQUIRED":
        st.error("⚠️ **Performance Notice:** Your average rating is below 2.5 on 5+ ratings. Your account is flagged for active performance review.")
