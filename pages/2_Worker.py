"""
2_Worker.py — Field Worker Portal.
Enables workers to register, log in, view assigned tasks, download AI planning checklists,
update job states, and upload completion proofs to trigger drone scanning.
Includes low-connectivity offline queue syncing controls.
"""
import streamlit as st
import time
import textwrap
import base64
import plotly.express as px
import pandas as pd
from config import WORKER_DEFAULT_PWD, PRIORITY_COLORS, PRIORITY_EMOJIS, SLA_HOURS, ISSUE_TYPES
from backend import gcp_manager
from backend import blockchain
from backend import pubsub_workers
from backend import maps_helper
# FIX-01: Safe offline_queue import — never crashes if function missing
try:
    from backend import offline_queue as _offline_queue
    _OFFLINE_QUEUE_OK = True
except ImportError:
    _offline_queue = None
    _OFFLINE_QUEUE_OK = False


def _safe_queue_size() -> int:
    """Safe wrapper — returns 0 if offline_queue or function is missing."""
    try:
        if _OFFLINE_QUEUE_OK:
            if hasattr(_offline_queue, "get_queue_size"):
                return _offline_queue.get_queue_size()
            elif hasattr(_offline_queue, "get_pending_count"):
                return _offline_queue.get_pending_count()
        return 0
    except Exception:
        return 0


def _safe_queue_stats() -> dict:
    """Safe wrapper — returns empty stats dict if offline_queue missing."""
    try:
        if _OFFLINE_QUEUE_OK and hasattr(_offline_queue, "get_queue_stats"):
            return _offline_queue.get_queue_stats()
        return {"total":0,"pending":0,"processing":0,"done":0,"failed":0}
    except Exception:
        return {"total":0,"pending":0,"processing":0,"done":0,"failed":0}


def _safe_get_all_queued() -> list:
    """Safe wrapper for retrieving queued items."""
    try:
        if _OFFLINE_QUEUE_OK:
            if hasattr(_offline_queue, "get_all_queued"):
                return _offline_queue.get_all_queued()
            elif hasattr(_offline_queue, "get_all_items"):
                items = _offline_queue.get_all_items()
                res = []
                for item in items:
                    if isinstance(item, dict) and "data" in item:
                        task_data = item["data"]
                        if isinstance(task_data, dict) and "payload" in task_data:
                            res.append(task_data)
                        else:
                            res.append({"payload": task_data})
                    else:
                        res.append(item)
                return res
            elif hasattr(_offline_queue, "get_pending_items"):
                return _offline_queue.get_pending_items()
        return []
    except Exception:
        return []


def _safe_queue_task(task: dict):
    """Safe wrapper to queue a task."""
    try:
        if _OFFLINE_QUEUE_OK:
            if hasattr(_offline_queue, "queue_task"):
                return _offline_queue.queue_task(task)
            elif hasattr(_offline_queue, "enqueue"):
                return _offline_queue.enqueue(task)
    except Exception:
        pass


def _safe_clear_queue():
    """Safe wrapper to clear completed/all items."""
    try:
        if _OFFLINE_QUEUE_OK:
            if hasattr(_offline_queue, "clear_queue"):
                return _offline_queue.clear_queue()
            elif hasattr(_offline_queue, "clear_done"):
                return _offline_queue.clear_done()
    except Exception:
        pass

# ── Custom Styling Injection ────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .worker-card {
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 22px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }
    
    .badge-preferred {
        background-color: #10B981;
        color: white;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: bold;
    }
    .badge-review {
        background-color: #EF4444;
        color: white;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: bold;
    }
    .badge-standard {
        background-color: #6B7280;
        color: white;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title("👷 Field Worker Portal")
st.subheader("Assigned Jobs & Repair Performance Verification")

st.sidebar.markdown("## 🏙️ Civic Solvers")
st.sidebar.markdown("*Smarter Cities. Faster Fixes. Transparent Governance.*")
st.sidebar.markdown("**Team:** Obsidian Ops / Indic Intelligence")
st.sidebar.markdown("**Lead:** Shreyas Patankar")
st.sidebar.markdown("**Institutes:** PRMITR & PRMCEM")
st.sidebar.markdown("---")
st.sidebar.markdown("*PU Code Hackathon 3.0 + AWS AI for Bharat*")
st.sidebar.markdown("---")

# ── Login Security Check & Registration ─────────────────────────────────────
worker_session = st.session_state.get("worker_session")

if not worker_session:
    st.info("🔒 Please Log In or Register below to access worker assignments.")
    tab_auth1, tab_auth2 = st.tabs(["🔐 Log In", "📝 Register Worker Account"])
    
    with tab_auth1:
        st.markdown("### Log In to Worker Account")
        w_id = st.text_input("Worker ID", placeholder="e.g. WRK-NAG-01")
        w_pwd = st.text_input("Password", type="password", placeholder="Enter password")
        
        if st.button("Unlock Job Queue", type="primary"):
            if w_pwd != WORKER_DEFAULT_PWD:
                st.error("❌ Incorrect password.")
            elif not w_id:
                st.error("❌ Worker ID is required.")
            else:
                # Query Firestore
                w_data = gcp_manager.get_worker_by_id(w_id)
                if w_data:
                    st.session_state.worker_session = {
                        "name": w_data.get("name"),
                        "worker_name": w_data.get("name"),
                        "full_name": w_data.get("name"),
                        "worker_id": w_data.get("worker_id"),
                        "city": w_data.get("city"),
                        "skills": w_data.get("skills", []),
                        "avg_rating": w_data.get("avg_rating", 5.0),
                        "total_ratings": w_data.get("total_ratings", 0),
                        "rating_sum": w_data.get("rating_sum", 0),
                        "completed_jobs": w_data.get("completed_jobs", 0),
                        "penalty_count": w_data.get("penalty_count", 0),
                        "performance_flag": w_data.get("performance_flag", "STANDARD"),
                    }
                    st.success(f"Log in successful. Welcome back, {w_data.get('name')}!")
                    st.rerun()
                else:
                    st.error("❌ Worker ID not found in database. Please register.")
                    
    with tab_auth2:
        st.markdown("### Register Worker Account")
        reg_name = st.text_input("Full Name", placeholder="Enter your full name")
        reg_worker_id = st.text_input("Desired Worker ID", placeholder="e.g. WRK-NAG-01")
        reg_pwd = st.text_input("Password Set", type="password", placeholder="e.g. worker123")
        reg_city = st.selectbox("City Jurisdiction", ["Nagpur", "Pune", "Mumbai", "Delhi", "Bengaluru"])
        reg_skills = st.multiselect("Skills / Certifications", ISSUE_TYPES)
        
        if st.button("Create Account", type="primary"):
            if not reg_name or not reg_worker_id or not reg_pwd or not reg_city or not reg_skills:
                st.error("❌ All fields are required.")
            elif reg_pwd != WORKER_DEFAULT_PWD:
                st.error(f"❌ For demo deployment, Password must match default password: {WORKER_DEFAULT_PWD}")
            else:
                # Check duplication
                if gcp_manager.get_worker_by_id(reg_worker_id):
                    st.error("❌ Worker ID is already taken. Please choose another one.")
                else:
                    try:
                        w_payload = {
                            "worker_id": reg_worker_id,
                            "name": reg_name,
                            "worker_name": reg_name,
                            "full_name": reg_name,
                            "city": reg_city,
                            "skills": reg_skills,
                            "avg_rating": 5.0,
                            "total_ratings": 0,
                            "rating_sum": 0,
                            "completed_jobs": 0,
                            "penalty_count": 0,
                            "performance_flag": "STANDARD",
                            "registered_at": gcp_manager.now_iso(),
                        }
                        gcp_manager.db.collection("workers").document(reg_worker_id).set(w_payload)
                        st.session_state.worker_session = {
                            "name": reg_name,
                            "worker_name": reg_name,
                            "full_name": reg_name,
                            "worker_id": reg_worker_id,
                            "city": reg_city,
                            "skills": reg_skills,
                            "avg_rating": 5.0,
                            "total_ratings": 0,
                            "rating_sum": 0,
                            "completed_jobs": 0,
                            "penalty_count": 0,
                            "performance_flag": "STANDARD",
                        }
                        st.success("✅ Worker account created. You can now view and accept jobs.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Account registration failed: {e}")

else:
    # ── Logged In Experience ─────────────────────────────────────────────────
    worker_name = worker_session.get('name') or worker_session.get('worker_name') or worker_session.get('full_name', 'Contractor')
    st.sidebar.markdown(f"### Logged In: {worker_name}")
    st.sidebar.markdown(f"**ID:** {worker_session['worker_id']}")
    st.sidebar.markdown(f"**City:** {worker_session['city']}")
    st.sidebar.markdown(f"**Average Rating:** ⭐ {worker_session['avg_rating']}")
    
    # Render Worker Status Badge
    flag = worker_session.get("performance_flag", "STANDARD")
    if flag == "PREFERRED":
         st.sidebar.markdown('<span class="badge-preferred">🌟 PREFERRED WORKER</span>', unsafe_allow_html=True)
    elif flag == "REVIEW_REQUIRED":
         st.sidebar.markdown('<span class="badge-review">⚠️ PERFORMANCE REVIEW</span>', unsafe_allow_html=True)
    else:
         st.sidebar.markdown('<span class="badge-standard">STANDARD WORKER</span>', unsafe_allow_html=True)

    if st.sidebar.button("Logout"):
        st.session_state.worker_session = None
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["📋 My Job Queue", "📤 Upload Repair Proof", "📈 My Rating Performance"])

    # ── TAB 1: JOB QUEUE ─────────────────────────────────────────────────────
    with tab1:
        st.markdown("### Assigned Tasks")
        
        # Check offline queue size
        q_size = _safe_queue_size()
        if q_size > 0:
            st.warning(f"📡 Low Connectivity Detected: You have {q_size} completed job(s) queued offline.")
            if st.button("🔄 Sync Offline Queue with Cloud", type="primary"):
                # Run sync logic
                items = _safe_get_all_queued()
                succeeded = 0
                for item in items:
                    try:
                        cid = item["payload"].get("complaint_id")
                        p = item["payload"]
                        raw_bytes = base64.b64decode(p["photo_base64"])
                        dest = f"complaints/{cid}/completion.{p['file_ext']}"
                        
                        # Upload GCS
                        gcs_uri = gcp_manager.upload_media_to_gcs(raw_bytes, dest, p["file_type"])
                        
                        gcp_manager.update_complaint_status(
                            cid, "COMPLETION_UPLOADED",
                            "Worker synced completion proof from offline queue. Drone scan triggered.",
                            worker_name,
                            {
                                "completion_photo_path": gcs_uri,
                                "completion_photo_hash": p["photo_hash"],
                                "completion_uploaded_at": gcp_manager.now_iso()
                            }
                        )
                        
                        blockchain.add_entry(cid, "COMPLETION_UPLOADED", worker_name, photo_hash=p["photo_hash"])
                        
                        # Trigger verifier
                        pubsub_workers.publish_event(
                            topic_id=gcp_manager.PUBSUB_TOPIC_ID,
                            payload={
                                "event_type": "COMPLETION_UPLOADED",
                                "complaint_id": cid,
                                "before_photo_path": p["before_photo_path"],
                                "after_photo_path": gcs_uri
                            }
                        )
                        succeeded += 1
                    except Exception as ex:
                        st.error(f"Sync error for task {item['payload'].get('complaint_id')}: {ex}")
                
                _safe_clear_queue()
                st.success(f"Successfully synced {succeeded} jobs with Cloud Services!")
                time.sleep(1)
                st.rerun()

        # Fetch assigned complaints
        all_comps = gcp_manager.get_all_complaints()
        active_jobs = [c for c in all_comps if c.get("assigned_worker_id") == worker_session["worker_id"] and c.get("status") in ("ASSIGNED", "ACCEPTED", "IN_PROGRESS", "REQUIRES_REWORK")]
        
        if not active_jobs:
            st.info("No active tasks assigned to you. Enjoy your day!")
        else:
            for job in active_jobs:
                cid = job["complaint_id"]
                status = job.get("status", "ASSIGNED")
                priority = job.get("priority", "MEDIUM")
                color = PRIORITY_COLORS.get(priority, "#9CA3AF")
                emoji = PRIORITY_EMOJIS.get(priority, "⚪")
                
                with st.container():
                    st.markdown(textwrap.dedent(f"""
                    <div class="worker-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h4 style="margin: 0; color: #1E3A8A;">📋 Job ID: {cid}</h4>
                            <span style="background-color: {color}; color: white; padding: 3px 8px; border-radius: 6px; font-weight: bold; font-size: 12px;">
                                {emoji} {priority} Priority ({status})
                            </span>
                        </div>
                        <div style="margin-top: 8px; font-size: 13px; color: #4B5563;">
                            <b>Location:</b> {job.get('location_text')} | <b>Ward:</b> {job.get('ward')}
                        </div>
                        <div style="margin-top: 5px; font-size: 13px; color: #4B5563;">
                            <b>ETA Deadline:</b> {job.get('resolution_eta')}
                        </div>
                    </div>
                    """), unsafe_allow_html=True)
                    
                    # AI Plan details
                    ai_analysis = job.get("ai_analysis", {})
                    planning = ai_analysis.get("planning", {})
                    if planning:
                        with st.expander("🛠️ View AI Planning Recommended Action Plan"):
                            st.write(f"**Recommended Team Size:** {planning.get('recommended_team_size', 3)} workers")
                            st.write(f"**Estimated Materials Required:** {', '.join(planning.get('required_materials', []))}")
                            st.write(f"**Estimated Cost:** ₹{planning.get('estimated_budget_inr', 0):,}")
                            st.write("**Repair Steps Checklist:**")
                            for step in planning.get("repair_steps", []):
                                st.checkbox(step, key=f"chk_{cid}_{step.replace(' ', '_')}")
                    
                    # Workflow buttons
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        btn_accept_disabled = (status != "ASSIGNED")
                        if st.button("Confirm Accept Job", key=f"btn_acc_{cid}", disabled=btn_accept_disabled, type="primary"):
                            gcp_manager.update_complaint_status(
                                cid, "ACCEPTED", "Worker accepted job assignment. Preparing tools.", 
                                worker_name, {"accepted_at": gcp_manager.now_iso()}
                            )
                            blockchain.add_entry(cid, "ACCEPTED", worker_name)
                            st.success("Job accepted!")
                            time.sleep(1)
                            st.rerun()
                            
                    with col_b2:
                        btn_start_disabled = (status not in ("ACCEPTED", "ASSIGNED"))
                        if st.button("Mark Work: IN PROGRESS", key=f"btn_start_{cid}", disabled=btn_start_disabled):
                            gcp_manager.update_complaint_status(
                                cid, "IN_PROGRESS", "Worker arrived on-site. Excavation/repair started.", 
                                worker_name, {"work_started_at": gcp_manager.now_iso()}
                            )
                            blockchain.add_entry(cid, "WORK_STARTED", worker_name)
                            st.success("Work started!")
                            time.sleep(1)
                            st.rerun()
                    
                    st.markdown("---")

    # ── TAB 2: UPLOAD REPAIR PROOF ───────────────────────────────────────────
    with tab2:
        st.markdown("### Upload Completion Proof")
        st.markdown("Submit a photograph of the repaired site to trigger automated drone verification.")
        
        all_comps = gcp_manager.get_all_complaints()
        uploadable_jobs = [c for c in all_comps if c.get("assigned_worker_id") == worker_session["worker_id"] and c.get("status") in ("ACCEPTED", "IN_PROGRESS", "REQUIRES_REWORK")]
        
        if not uploadable_jobs:
            st.info("No active tasks in progress. You must accept and start a job first.")
        else:
            selected_job_id = st.selectbox("Select Active Job ID", [c["complaint_id"] for c in uploadable_jobs])
            selected_job = next(c for c in uploadable_jobs if c["complaint_id"] == selected_job_id)
            
            st.image(selected_job["photo_path"], caption="Before photo uploaded by citizen", width=300)
            
            uploaded_proof = st.file_uploader("Upload Completion Photo (JPG/PNG)", type=["jpg", "jpeg", "png"])
            network_online = st.toggle("Simulate Network Online", value=True)
            
            if uploaded_proof:
                st.image(uploaded_proof, caption="After photo preview", width=300)
                
                if st.button("Submit Completion Proof", type="primary"):
                    file_bytes = uploaded_proof.read()
                    proof_hash = gcp_manager.hash_file_bytes(file_bytes)
                    file_ext = uploaded_proof.name.split(".")[-1]
                    
                    payload = {
                        "event_type": "COMPLETION_UPLOADED",
                        "complaint_id": selected_job["complaint_id"],
                        "before_photo_path": selected_job["photo_path"],
                    }
                    
                    if network_online:
                        # Online path
                        destination_name = f"complaints/{selected_job['complaint_id']}/completion.{file_ext}"
                        gcs_uri = gcp_manager.upload_media_to_gcs(file_bytes, destination_name, uploaded_proof.type)
                        
                        payload["after_photo_path"] = gcs_uri
                        
                        # Update complaint
                        gcp_manager.update_complaint_status(
                            selected_job["complaint_id"], "COMPLETION_UPLOADED",
                            "Worker uploaded completion proof. Drone scan triggered.",
                            worker_name,
                            {
                                "completion_photo_path": gcs_uri,
                                "completion_photo_hash": proof_hash,
                                "completion_uploaded_at": gcp_manager.now_iso(),
                                "status": "COMPLETION_UPLOADED"
                            }
                        )
                        
                        # Blockchain
                        blockchain.add_entry(
                            selected_job["complaint_id"], "COMPLETION_UPLOADED", worker_name,
                            photo_hash=proof_hash
                        )
                        
                        # PubSub event to trigger verifier
                        pubsub_workers.publish_event(
                            topic_id=gcp_manager.PUBSUB_TOPIC_ID,
                            payload=payload
                        )
                        
                        st.success("🎉 Completion proof uploaded successfully! Drone verifier queued.")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        # Offline path — queue in local SQLite/JSON
                        b64_data = base64.b64encode(file_bytes).decode("utf-8")
                        _safe_queue_task({
                            "complaint_id": selected_job["complaint_id"],
                            "before_photo_path": selected_job["photo_path"],
                            "photo_base64": b64_data,
                            "photo_hash": proof_hash,
                            "file_ext": file_ext,
                            "file_type": uploaded_proof.type
                        })
                        
                        # Local UI feedback only, don't update Cloud Firestore
                        st.warning("📡 Saved in offline queue. This proof will be submitted automatically when connectivity is restored.")

    # ── TAB 3: PERFORMANCE ───────────────────────────────────────────────────
    with tab3:
        st.markdown("### Reputation Dashboard")
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("Your Average Rating", f"⭐ {worker_session['avg_rating']} / 5.0")
            st.metric("Total Completed Jobs", worker_session.get("completed_jobs", 0))
        
        with col_m2:
            st.metric("SLA Penalties", worker_session.get("penalty_count", 0))
            st.metric("Performance Status", flag)
            
        if flag == "REVIEW_REQUIRED":
            st.error("⚠️ **Performance Notice:** Your average rating is below 2.5 on 5+ jobs. Your account is flagged for active performance review.")

        # Plotly chart
        st.markdown("#### Job Completion Rating History")
        
        # Fetch individual worker ratings
        try:
            r_docs = gcp_manager.db.collection("worker_ratings").where("worker_id", "==", worker_session["worker_id"]).stream()
            ratings = [doc.to_dict() for doc in r_docs]
        except Exception:
            ratings = []
            
        if not ratings:
            st.info("No ratings logged yet. Complete jobs to receive feedback from citizens.")
        else:
            # Prepare dataframe
            df_data = []
            for r in ratings:
                df_data.append({
                    "Date": r.get("rated_at", "")[:10],
                    "Rating": r.get("rating", 5),
                    "Comment": r.get("comment", "")
                })
            
            df = pd.DataFrame(df_data)
            fig = px.bar(df, x="Date", y="Rating", color="Rating",
                         title="Ratings Trend", color_continuous_scale="Viridis", height=300)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("#### Citizen Comments")
            for idx, row in df.iterrows():
                if row['Comment']:
                    st.markdown(f"- *{row['Date']}:* **⭐ {row['Rating']}** — \"{row['Comment']}\"")
