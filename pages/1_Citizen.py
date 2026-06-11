"""
1_Citizen.py — Citizen Portal.
Allows citizens to register, submit issues, track progress with a 7-step visual timeline,
view blockchain verification ledgers, and manage their gamification scores/ranks.
"""
import streamlit as st
import base64
import time
import textwrap
from datetime import datetime
from config import ISSUE_TYPES, PRIORITY_COLORS, PRIORITY_EMOJIS, COMPLAINT_STATUSES, CIVIC_TIERS
from backend import gcp_manager
from backend import blockchain
from backend import gamification
from backend import pubsub_workers
from backend import maps_helper

# ── Custom Styling Injection ────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .card {
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
    }
    
    .progress-bar-container {
        display: flex;
        justify-content: space-between;
        margin: 20px 0;
        position: relative;
    }
    .progress-bar-line {
        position: absolute;
        top: 15px;
        left: 5%;
        right: 5%;
        height: 4px;
        background-color: #E5E7EB;
        z-index: 1;
    }
    .progress-bar-fill {
        position: absolute;
        top: 15px;
        left: 5%;
        height: 4px;
        background-color: #3B82F6;
        z-index: 2;
        transition: width 0.4s ease;
    }
    .progress-step {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background-color: #FFFFFF;
        border: 3px solid #E5E7EB;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 3;
        font-weight: bold;
        font-size: 12px;
        color: #9CA3AF;
        transition: all 0.3s ease;
    }
    .progress-step.active {
        border-color: #3B82F6;
        background-color: #3B82F6;
        color: #FFFFFF;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
    }
    .progress-step.completed {
        border-color: #10B981;
        background-color: #10B981;
        color: #FFFFFF;
    }
    
    .timeline-title {
        font-size: 11px;
        text-align: center;
        margin-top: 5px;
        max-width: 75px;
        color: #4B5563;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

st.title("🧑‍💼 Citizen Portal")
st.subheader("Smarter Cities. Transparent Governance. Earn Rewards.")

st.sidebar.markdown("## 🏙️ Civic Solvers")
st.sidebar.markdown("*Smarter Cities. Faster Fixes. Transparent Governance.*")
st.sidebar.markdown("**Team:** Obsidian Ops / Indic Intelligence")
st.sidebar.markdown("**Lead:** Shreyas Patankar")
st.sidebar.markdown("**Institutes:** PRMITR & PRMCEM")
st.sidebar.markdown("---")
st.sidebar.markdown("*PU Code Hackathon 3.0 + AWS AI for Bharat*")
st.sidebar.markdown("---")

# ── Login & Session Management ──────────────────────────────────────────────
session = st.session_state.get("citizen_session")

if not session:
    st.info("🔒 Please Register or Log In below to access citizen services.")
    tab_auth1, tab_auth2 = st.tabs(["🔐 Login", "📝 Register New Account"])
    
    with tab_auth1:
        st.markdown("### Log In to Your Account")
        login_phone = st.text_input("Registered Phone Number", key="login_phone", placeholder="Enter 10-digit mobile number")
        login_aadhar = st.text_input("Aadhar Card Number", type="password", key="login_aadhar", placeholder="Enter 12-digit Aadhar")
        
        if st.button("Access Account", type="primary"):
            if len(login_phone) == 10 and len(login_aadhar) == 12:
                aadhar_hash = gcp_manager.hash_identifier(login_aadhar)
                citizen = gcp_manager.get_complaint_by_id(aadhar_hash) # Get doc from citizens collection (aadhar_hash is doc ID)
                # Wait, get_complaint_by_id is for complaints. Let's retrieve from database directly.
                try:
                    c_doc = gcp_manager.db.collection("citizens").document(aadhar_hash).get()
                    if c_doc.exists:
                        c_data = c_doc.to_dict()
                        phone_hash = gcp_manager.hash_identifier(login_phone, salt="phone_salt_v1")
                        if c_data.get("phone_hash") == phone_hash:
                            if c_data.get("active", True):
                                c_payload = {
                                    "name": c_data.get("name"),
                                    "citizen_name": c_data.get("name"),
                                    "full_name": c_data.get("name"),
                                    "aadhar_hash": aadhar_hash,
                                    "phone": login_phone,
                                    "phone_display": c_data.get("phone_display") or ("*" * 6) + str(login_phone)[-4:],
                                    "city": c_data.get("city"),
                                    "ward": c_data.get("ward"),
                                    "tier": c_data.get("tier", "🥉 Bronze Citizen"),
                                    "total_points": c_data.get("total_points", 0),
                                }
                                st.session_state.citizen_session = c_payload
                                st.success(f"Welcome back, {c_payload['name']}!")
                                st.rerun()
                            else:
                                st.error(f"❌ Account suspended: {c_data.get('suspension_reason', 'Policy violation')}")
                        else:
                            st.error("❌ Phone number and Aadhar combination is incorrect.")
                    else:
                        st.error("❌ No account found with this Aadhar number. Please verify input or register.")
                except Exception as e:
                    st.error(f"❌ Login error: {e}")
            else:
                st.error("❌ Enter valid 10-digit phone number and 12-digit Aadhar number.")

    with tab_auth2:
        st.markdown("### Register Account (Salted Aadhar Gate)")
        reg_name = st.text_input("Full Name", placeholder="Enter your full name")
        reg_city = st.selectbox("City", ["Nagpur", "Pune", "Mumbai", "Delhi", "Bengaluru"])
        reg_ward = st.text_input("Ward Number", placeholder="e.g. Ward 12")
        reg_phone = st.text_input("Phone Number", placeholder="10-digit mobile number")
        reg_aadhar = st.text_input("Mock Aadhar Number", type="password", placeholder="12-digit Aadhar number")
        
        st.caption("🔒 *Identity Verification Gate: Your Aadhar number is cryptographically salted & hashed. Raw numbers are never written.*")

        if st.button("Create Account", type="primary"):
            if not reg_name or not reg_phone or not reg_aadhar or not reg_ward:
                st.error("❌ All fields are required.")
            elif len(reg_phone) != 10:
                st.error("❌ Phone number must be 10 digits.")
            elif len(reg_aadhar) != 12 or not reg_aadhar.isdigit():
                st.error("❌ Aadhar number must be a 12-digit number.")
            else:
                aadhar_hash = gcp_manager.hash_identifier(reg_aadhar)
                
                # Check duplication
                if gcp_manager.citizen_exists_by_aadhar(aadhar_hash):
                    st.error("❌ Duplicate Aadhar: An account already exists with this Aadhar number.")
                elif gcp_manager.citizen_exists_by_phone(reg_phone):
                    st.error("❌ Duplicate Phone: Phone number already registered.")
                else:
                    try:
                        registered = gcp_manager.register_citizen(aadhar_hash, reg_phone, reg_name, reg_city, reg_ward)
                        st.session_state.citizen_session = {
                            "name": reg_name,
                            "citizen_name": reg_name,
                            "full_name": reg_name,
                            "aadhar_hash": aadhar_hash,
                            "phone": reg_phone,
                            "phone_display": ("*" * 6) + str(reg_phone)[-4:],
                            "city": reg_city,
                            "ward": reg_ward,
                            "tier": "🥉 Bronze Citizen",
                            "total_points": 0,
                        }
                        st.success(f"✅ Welcome {reg_name}! Account created. You can now file complaints.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Registration failed: {e}")

else:
    # ── Logged In Experience ─────────────────────────────────────────────────
    st.sidebar.markdown(f"### Logged In: {session.get('name') or session.get('citizen_name') or session.get('full_name', 'User')}")
    st.sidebar.markdown(f"**City:** {session['city']} | **Ward:** {session['ward']}")
    st.sidebar.markdown(f"**Tier:** {session['tier']}")
    
    if st.sidebar.button("Logout"):
        st.session_state.citizen_session = None
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["✍️ File a Complaint", "📋 Track My Complaints", "🏆 My Civic Score & Leaderboard"])

    # ── TAB 1: FILE A COMPLAINT ──────────────────────────────────────────────
    with tab1:
        st.markdown("### Report a Civic Issue")
        st.markdown("Submit a verified photo to trigger the autonomous routing pipeline in under 30 seconds.")
        
        # FIX-02: GPS AUTO-EXTRACTION FROM PHOTO EXIF
        from backend.gps_extractor import extract_gps_from_uploaded_file

        photo = st.file_uploader(
            "📷 Photo of the issue",
            type=["jpg", "jpeg", "png", "heic"],
            help="Upload a photo taken on your phone. "
                 "If location was enabled when you took it, "
                 "GPS coordinates will fill in automatically.",
        )

        uploaded_file = photo

        # Default GPS values (Nagpur city centre as fallback)
        _default_lat = 20.925500
        _default_lon = 77.766300

        # GPS extraction state — stored in session so it persists across reruns
        if "gps_lat" not in st.session_state:
            st.session_state["gps_lat"] = _default_lat
        if "gps_lon" not in st.session_state:
            st.session_state["gps_lon"] = _default_lon
        if "gps_source" not in st.session_state:
            st.session_state["gps_source"] = "manual"
        if "gps_message" not in st.session_state:
            st.session_state["gps_message"] = ""
        if "last_photo_name" not in st.session_state:
            st.session_state["last_photo_name"] = None

        if photo is not None:
            # Show photo preview
            st.image(photo, caption="📸 Photo Preview", use_container_width=True)

            # Only re-extract GPS if the photo changed (avoid re-running on every widget change)
            if photo.name != st.session_state.get("last_photo_name"):
                st.session_state["last_photo_name"] = photo.name

                with st.spinner("🔍 Reading GPS location from photo..."):
                    gps_result = extract_gps_from_uploaded_file(photo)

                if gps_result["found"]:
                    # Auto-fill coordinates from EXIF
                    st.session_state["gps_lat"]     = gps_result["latitude"]
                    st.session_state["gps_lon"]     = gps_result["longitude"]
                    st.session_state["gps_source"]  = "exif"
                    st.session_state["gps_message"] = gps_result["message"]
                else:
                    # Keep previous coordinates, show reason
                    st.session_state["gps_source"]  = "manual"
                    st.session_state["gps_message"] = gps_result["message"]

            # Show GPS status banner
            if st.session_state["gps_source"] == "exif":
                st.success(st.session_state["gps_message"])
            else:
                if st.session_state["gps_message"]:
                    st.info(
                        f"ℹ️ {st.session_state['gps_message']} "
                        "You can adjust the coordinates below manually."
                    )

        else:
            # No photo uploaded — reset GPS to defaults
            if st.session_state.get("last_photo_name") is not None:
                st.session_state["gps_lat"]        = _default_lat
                st.session_state["gps_lon"]        = _default_lon
                st.session_state["gps_source"]     = "manual"
                st.session_state["gps_message"]    = ""
                st.session_state["last_photo_name"]= None

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            issue_type = st.selectbox("Issue Classification", ISSUE_TYPES)
            description = st.text_area("Detailed Description", placeholder="Describe the severity and location details...")
            loc_text = st.text_input("Street Address / Landmark", placeholder="e.g. Near PRMITR main gate, Badnera road")
        
        with col_f2:
            # ── GPS COORDINATE INPUTS ────────────────────────────────────
            st.markdown("**📍 GPS Location Coordinates**")

            _is_from_exif = st.session_state["gps_source"] == "exif"

            if _is_from_exif:
                st.markdown(
                    f"🛰️ **Auto-detected from photo EXIF** — "
                    f"`{st.session_state['gps_lat']:.6f}, {st.session_state['gps_lon']:.6f}`"
                )
                st.caption("You can still adjust if needed.")

            col_lat, col_lon = st.columns(2)
            with col_lat:
                latitude = st.number_input(
                    "Latitude",
                    value=float(st.session_state["gps_lat"]),
                    min_value=-90.0,
                    max_value=90.0,
                    format="%.6f",
                    key="input_lat",
                    help="Auto-filled from photo GPS. Edit manually if needed.",
                )
            with col_lon:
                longitude = st.number_input(
                    "Longitude",
                    value=float(st.session_state["gps_lon"]),
                    min_value=-180.0,
                    max_value=180.0,
                    format="%.6f",
                    key="input_lon",
                    help="Auto-filled from photo GPS. Edit manually if needed.",
                )

            # Keep session in sync with manual edits
            st.session_state["gps_lat"] = latitude
            st.session_state["gps_lon"] = longitude

            lat_input = latitude
            lng_input = longitude

            # ── GPS VERIFIED BADGE ───────────────────────────────────────
            if _is_from_exif:
                st.markdown(
                    "🟢 **GPS Verified** — location extracted directly from photo metadata. "
                    "This increases complaint credibility in AI audit."
                )
            else:
                st.markdown(
                    "🟡 **Manual GPS** — coordinates entered by user. "
                    "Upload a geotagged photo to auto-verify location."
                )
            
            # Simulated Hazard Flags for testing
            st.markdown("**Proximity Hazards (AI Verification Inputs)**")
            near_school = st.checkbox("Within school zone (500m)")
            near_hospital = st.checkbox("Within hospital zone (500m)")
            heavy_traffic = st.checkbox("Arterial road / Heavy traffic lane")

        if st.button("Submit Complaint to Blockchain Ledger", type="primary"):
            if not uploaded_file:
                st.error("❌ Please upload a photo of the issue.")
            elif not loc_text or not description:
                st.error("❌ Please specify landmark and detailed description.")
            else:
                try:
                    file_bytes = uploaded_file.read()
                    photo_hash = gcp_manager.hash_file_bytes(file_bytes)
                    
                    # Upload file to GCS Mock or Real
                    cid = gcp_manager.generate_cid()
                    file_ext = uploaded_file.name.split(".")[-1]
                    destination_name = f"complaints/{cid}/original.{file_ext}"
                    
                    gcs_uri = gcp_manager.upload_media_to_gcs(file_bytes, destination_name, uploaded_file.type)
                    
                    metadata = {
                        "citizen_aadhar_hash": session["aadhar_hash"],
                        "citizen_name": session.get('name') or session.get('citizen_name') or session.get('full_name', 'User'),
                        "issue_type": issue_type,
                        "location_text": loc_text,
                        "latitude": lat_input,
                        "longitude": lng_input,
                        "ward": session["ward"],
                        "city": session["city"],
                        "near_school": near_school,
                        "near_hospital": near_hospital,
                        "heavy_traffic_road": heavy_traffic,
                        "photo_path": gcs_uri,
                        "photo_hash": photo_hash
                    }
                    
                    # Create complaint document in Firestore
                    complaint = gcp_manager.build_complaint(
                        session["aadhar_hash"], session.get('name') or session.get('citizen_name') or session.get('full_name', 'User'), session["phone_display"],
                        session["city"], session["ward"], issue_type, description,
                        loc_text, lat_input, lng_input, gcs_uri, photo_hash
                    )
                    
                    # Write blockchain submit entry
                    blockchain.add_entry(
                        complaint["complaint_id"], "COMPLAINT_SUBMITTED", session.get('name') or session.get('citizen_name') or session.get('full_name', 'User'),
                        photo_hash=photo_hash, metadata={"location_text": loc_text}
                    )
                    
                    # Run full AI pipeline synchronously so the tracker advances immediately
                    from backend.ai_engine import run_full_ai_pipeline
                    with st.spinner("🤖 Orchestrating multi-agent AI pipeline (Vision, Risk, Memory, Planning)..."):
                        try:
                            run_full_ai_pipeline(complaint["complaint_id"], file_bytes, metadata)
                        except Exception as ai_err:
                            st.warning(f"⚠️ AI pipeline sync execution warning: {ai_err}")
                            
                    # Update local session stats for total complaints count
                    try:
                        c_ref = gcp_manager.db.collection("citizens").document(session["aadhar_hash"])
                        c_ref.update({"total_complaints": gcp_manager.firestore_lib.Increment(1) if hasattr(gcp_manager.firestore_lib, "Increment") else session.get("total_complaints", 0) + 1})
                        # Refresh session dict
                        updated_doc = c_ref.get().to_dict()
                        if updated_doc:
                            st.session_state.citizen_session = updated_doc
                    except Exception:
                        pass
                    
                    # Publish Pub/Sub event for async AI Pipeline
                    pubsub_workers.publish_event(
                        topic_id=gcp_manager.PUBSUB_TOPIC_ID,
                        payload={
                            "event_type": "NEW_COMPLAINT",
                            "complaint_id": complaint["complaint_id"],
                            "metadata": metadata
                        }
                    )
                    
                    st.success(f"🎉 Submitted & AI Analyzed! Complaint ID: {complaint['complaint_id']}")
                    st.info("🤖 Assigned immediately. Check 'Track My Complaints' tab.")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to submit complaint: {e}")

    # ── TAB 2: TRACK MY COMPLAINTS ───────────────────────────────────────────
    with tab2:
        st.markdown("### Active & Historic Filings")
        
        # Stream user complaints
        my_complaints = gcp_manager.get_all_complaints({"citizen_aadhar_hash": session["aadhar_hash"]})
        
        if not my_complaints:
            st.info("You haven't filed any complaints yet. Use the 'File a Complaint' tab to start.")
        else:
            # Sort by submitted date descending
            my_complaints.sort(key=lambda x: x.get("submitted_at", ""), reverse=True)
            
            for comp in my_complaints:
                cid = comp.get("complaint_id")
                status = comp.get("status", "PENDING")
                priority = comp.get("priority", "PENDING")
                submitted_at = comp.get("submitted_at", "")[:19].replace("T", " ")
                
                color = PRIORITY_COLORS.get(priority, "#9CA3AF")
                emoji = PRIORITY_EMOJIS.get(priority, "⚪")

                with st.container():
                    st.markdown(textwrap.dedent(f"""
                    <div class="card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h4 style="margin: 0; color: #1E3A8A;">📋 Complaint ID: {cid}</h4>
                            <span style="background-color: {color}; color: white; padding: 3px 8px; border-radius: 6px; font-weight: bold; font-size: 12px;">
                                {emoji} {priority} Priority
                            </span>
                        </div>
                        <div style="margin-top: 8px; font-size: 13px; color: #4B5563;">
                            <b>Type:</b> {comp.get('issue_type')} | <b>Location:</b> {comp.get('location_text')} | <b>Filed:</b> {submitted_at}
                        </div>
                    </div>
                    """), unsafe_allow_html=True)
                    
                    # 7-Step Visual Tracker Logic
                    # Steps: PENDING, AI_ANALYZING, ASSIGNED, IN_PROGRESS, COMPLETION_UPLOADED, DRONE_SCANNING, VERIFIED_COMPLETE (or CLOSED)
                    tracker_steps = [
                        ("PENDING", "Submitted"),
                        ("AI_ANALYZING", "AI Audit"),
                        ("ASSIGNED", "Assigned"),
                        ("IN_PROGRESS", "Repairing"),
                        ("COMPLETION_UPLOADED", "Finished"),
                        ("DRONE_SCANNING", "Drone scan"),
                        ("VERIFIED_COMPLETE", "Verified")
                    ]
                    
                    # Find index of current status in tracker
                    status_map = {
                        "PENDING": 0,
                        "AI_ANALYZING": 1,
                        "FAKE_DETECTED": 0,
                        "ASSIGNED": 2,
                        "ACCEPTED": 2,
                        "IN_PROGRESS": 3,
                        "WORK_STARTED": 3,
                        "REQUIRES_REWORK": 3,
                        "COMPLETION_UPLOADED": 4,
                        "DRONE_SCANNING": 5,
                        "VERIFIED_COMPLETE": 6,
                        "CLOSED": 6,
                        "CITIZEN_RATED": 6,
                        "ESCALATED": 2
                    }
                    current_idx = status_map.get(status, 0)
                            
                    # Construct progress bar HTML
                    steps_html = ""
                    fill_pct = int((current_idx / (len(tracker_steps) - 1)) * 90) if len(tracker_steps) > 1 else 0
                    
                    for idx, (s_code, s_label) in enumerate(tracker_steps):
                        step_class = "progress-step"
                        if idx < current_idx:
                            step_class += " completed"
                        elif idx == current_idx:
                            step_class += " active"
                        
                        steps_html += f'<div style="display: flex; flex-direction: column; align-items: center; z-index: 3;"><div class="{step_class}">{idx+1}</div><div class="timeline-title">{s_label}</div></div>'
                        
                    st.markdown(f'<div class="progress-bar-container"><div class="progress-bar-line"></div><div class="progress-bar-fill" style="width: {fill_pct}%;"></div>{steps_html}</div>', unsafe_allow_html=True)
                    
                    # Status text
                    st.info(f"📍 **Status Note:** {comp['status_history'][-1]['note']}")
                    
                    # Expandable details
                    with st.expander("🔍 Drill Down Detail & Blockchain Ledger Proofs"):
                        col_d1, col_d2 = st.columns(2)
                        with col_d1:
                            st.write(f"**Issue Description:** {comp.get('description')}")
                            st.write(f"**Resolution Timeline ETA:** {comp.get('resolution_eta')}")
                            st.write(f"**Assigned Department:** {comp.get('assigned_department', 'Routing in progress')}")
                            
                            ai_analysis = comp.get("ai_analysis", {})
                            if ai_analysis:
                                st.write("**AI Vision Agent Verdict:**")
                                st.caption(ai_analysis.get("vision", {}).get("ai_description", "No visual desc."))
                                
                                planning = ai_analysis.get("planning", {})
                                if planning:
                                    st.write("**Planning Agent Recommended Action Plan:**")
                                    for step in planning.get("repair_steps", []):
                                        st.caption(step)
                        
                        with col_d2:
                            # Show original image vs completion image side by side
                            img_cols = st.columns(2)
                            with img_cols[0]:
                                path_original = comp.get("photo_path")
                                if path_original:
                                    # Fetch from mock blob
                                    try:
                                        bytes_orig = maps_helper.download_gcs_bytes(path_original)
                                        st.image(bytes_orig, caption="Reported Photo", use_container_width=True)
                                    except Exception:
                                        st.caption("📷 Photo uploaded to Storage")
                            with img_cols[1]:
                                path_completion = comp.get("completion_photo_path")
                                if path_completion:
                                    try:
                                        bytes_comp = maps_helper.download_gcs_bytes(path_completion)
                                        st.image(bytes_comp, caption="Resolution Photo", use_container_width=True)
                                    except Exception:
                                        st.caption("📷 Completion Photo uploaded")

                        st.markdown("##### 🔗 Cryptographic Blockchain Ledger Audit Trail")
                        ledger_entries = blockchain.get_complaint_ledger(cid)
                        if ledger_entries:
                            for entry in ledger_entries:
                                st.code(
                                    f"Event: {entry['event']} | Actor: {entry['actor']} | Timestamp: {entry['timestamp']}\n"
                                    f"Photo Hash: {entry['photo_hash'] or 'N/A'}\n"
                                    f"Prev Link Hash: {entry['prev_hash'][:24]}...",
                                    language="yaml"
                                )
                        else:
                            st.caption("No ledger events written yet.")

                    # Rating section
                    if status in ("VERIFIED_COMPLETE", "REQUIRES_REWORK") and comp.get("citizen_rating") is None:
                        st.markdown("#### ⭐ Rate the Repair Work Quality")
                        rating_score = st.slider(f"Rate resolution for complaint {cid}", min_value=1, max_value=5, value=5, key=f"slide_{cid}")
                        rating_comment = st.text_input("Comments (Optional)", placeholder="Describe work quality...", key=f"comm_{cid}")
                        
                        if st.button("Submit Feedback", key=f"btn_rate_{cid}", type="primary"):
                            worker_id = comp.get("assigned_worker_id")
                            if worker_id:
                                from backend import worker_reputation
                                res_rating = worker_reputation.record_citizen_rating(worker_id, cid, rating_score, rating_comment)
                                if "error" not in res_rating:
                                    # Update complaint rating
                                    gcp_manager.db.collection("complaints").document(cid).update({
                                        "citizen_rating": rating_score,
                                        "citizen_rating_comment": rating_comment,
                                        "citizen_rated_at": gcp_manager.now_iso(),
                                        "status": "CLOSED" # Move to closed once rated
                                    })
                                    # Award points for rating
                                    gamification.award_points(session["aadhar_hash"], "citizen_quality_confirmed", "Submitted quality review of completed job", cid)
                                    st.success("Thank you for your rating! Points awarded.")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(f"Error submitting rating: {res_rating['error']}")
                            else:
                                st.error("No assigned worker found to rate.")
                    st.markdown("---")

    # ── TAB 3: MY CIVIC SCORE ────────────────────────────────────────────────
    with tab3:
        stats = gamification.get_citizen_stats(session["aadhar_hash"])
        
        if "error" in stats:
            st.error(f"Failed to fetch reputation data: {stats['error']}")
        else:
            col_s1, col_s2 = st.columns(2)
            
            with col_s1:
                st.markdown(textwrap.dedent(f"""
                <div style="background-color: {stats['color']}1F; border: 2px solid {stats['color']}; border-radius: 12px; padding: 25px; text-align: center; margin-bottom: 20px;">
                    <h2 style="margin: 0; color: #1F2937;">{stats['tier']}</h2>
                    <h4 style="margin: 5px 0 0 0; color: {stats['color']}; font-weight: 600;">🎖️ {stats['badge']}</h4>
                    <h1 style="font-size: 48px; margin: 15px 0 0 0; color: #1F2937;">{stats['points']}</h1>
                    <span style="font-size: 14px; color: #6B7280; font-weight: 500;">TOTAL CIVIC POINTS EARNED</span>
                </div>
                """), unsafe_allow_html=True)
                # Progress to next level
                if stats["next_tier"] != "Max Tier":
                    st.markdown(f"**Progress to {stats['next_tier']}**")
                    st.progress(stats["progress"] / 100.0)
                    st.caption(f"📈 Need **{stats['points_needed']}** more points to level up.")
                else:
                    st.success("🏆 You are at the highest Diamond Legend tier! Cities salutes your civic leadership!")

                if stats["strikes"] > 0:
                    st.warning(f"⚠️ **Account Warning:** You have {stats['strikes']}/3 fake report strikes. 3 strikes will lead to account suspension.")

            with col_s2:
                st.markdown("#### 🏆 Nagpur City-Wide Leaderboard")
                leaders = gamification.get_leaderboard(limit=5)
                
                if not leaders:
                    st.caption("No leaderboard data available.")
                else:
                    for idx, c in enumerate(leaders):
                        medals = ["🥇", "🥈", "🥉", "🏅", "🏅"]
                        medal = medals[idx] if idx < len(medals) else "🏅"
                        points = c.get("total_points", 0)
                        
                        tier_name = "🥉 Bronze Citizen"
                        for tier in CIVIC_TIERS:
                            if tier["min"] <= points <= tier["max"]:
                                tier_name = tier["name"]
                                break
                        
                        is_current = (c.get("aadhar_hash") == session["aadhar_hash"])
                        
                        with st.container():
                            col_lb1, col_lb2, col_lb3 = st.columns([1.5, 3.5, 2])
                            with col_lb1:
                                if is_current:
                                    st.markdown(f"🌟 **{medal} #{idx+1}**")
                                else:
                                    st.markdown(f"{medal} #{idx+1}")
                            with col_lb2:
                                if is_current:
                                    st.markdown(f"**{c.get('name')} (You)**")
                                else:
                                    st.markdown(c.get('name'))
                                st.caption(tier_name)
                            with col_lb3:
                                st.markdown(f"**{points} pts**")
                            st.markdown("---")

            st.markdown("### 📜 Gamification Activity Logs")
            history = stats.get("history", [])
            if not history:
                st.caption("No points awarded yet.")
            else:
                hist_data = []
                for h in history:
                    ts = h.get("timestamp", "")[:19].replace("T", " ")
                    pts = f"+{h.get('points_awarded')}" if h.get("points_awarded", 0) >= 0 else str(h.get("points_awarded"))
                    hist_data.append({
                        "Timestamp": ts,
                        "Event Category": h.get("rule_key").replace("_", " ").title(),
                        "Change": pts,
                        "Reason": h.get("reason"),
                        "Complaint Linked": h.get("complaint_id", "N/A")
                    })
                st.table(hist_data)
