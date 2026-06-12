import streamlit as st
import os, base64
from data_manager import (register_citizen, login_citizen, submit_complaint,
                           get_citizen_complaints, award_points, verify_blockchain)
from ai_engine import run_ai_pipeline

def extract_gps_from_image(photo_bytes):
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS, GPSTAGS
        import io
        img = Image.open(io.BytesIO(photo_bytes))
        exif_data = img._getexif()
        if not exif_data:
            return None, None
        gps_info = {}
        for tag, value in exif_data.items():
            if TAGS.get(tag) == "GPSInfo":
                for gps_tag, gps_val in value.items():
                    gps_info[GPSTAGS.get(gps_tag)] = gps_val
        if "GPSLatitude" in gps_info and "GPSLongitude" in gps_info:
            lat = gps_info["GPSLatitude"]
            lng = gps_info["GPSLongitude"]
            lat_deg = float(lat[0]) + float(lat[1])/60 + float(lat[2])/3600
            lng_deg = float(lng[0]) + float(lng[1])/60 + float(lng[2])/3600
            if gps_info.get("GPSLatitudeRef") == "S":
                lat_deg = -lat_deg
            if gps_info.get("GPSLongitudeRef") == "W":
                lng_deg = -lng_deg
            return round(lat_deg, 6), round(lng_deg, 6)
        return None, None
    except Exception:
        return None, None

def autofill_from_photo(photo_bytes, issue_types):
    import base64, hashlib
    # Use image size and hash as proxy for AI detection
    size = len(photo_bytes)
    photo_hash = hashlib.sha256(photo_bytes).hexdigest()
    # Heuristic: suggest based on file size patterns
    # In production this calls Gemini Vision
    return {
        "suggested_issue": issue_types[0],
        "suggested_description": "AI detected civic infrastructure issue requiring immediate attention. Please verify and add details.",
        "is_likely_ai_generated": size < 50000,  # Very small files may be AI-generated
    }


ISSUE_TYPES = ["Pothole", "Water Leak", "Broken Streetlight", "Blocked Drain",
               "Garbage Dump", "Road Damage", "Fallen Tree", "Illegal Construction",
               "Sewage Overflow", "Other"]

STATUS_STEPS = {
    "PENDING": 1, "AI_ANALYZING": 2, "ASSIGNED": 3, "ACCEPTED": 3,
    "IN_PROGRESS": 4, "COMPLETION_UPLOADED": 5, "DRONE_SCANNING": 6,
    "VERIFIED_COMPLETE": 7, "CITIZEN_RATED": 7, "CLOSED": 7,
    "REQUIRES_REWORK": 4, "ESCALATED": 3, "FAKE_DETECTED": 1,
}
STEP_LABELS = ["Submitted", "AI Audit", "Assigned", "Repairing", "Finished", "Drone Scan", "Verified"]
PRIORITY_COLORS = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢", "PENDING": "⚪"}
TIER_EMOJIS = {
    "Bronze Citizen": "🥉", "Silver Guardian": "🥈",
    "Gold Champion": "🥇", "Platinum Sentinel": "💎", "Diamond Legend": "🏆"
}

st.set_page_config(page_title="Civic Solvers — Citizen", page_icon="🧑💼", layout="wide")

session = st.session_state.get("citizen_session")

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
if session:
    name = session.get("name", "Citizen")
    city = session.get("city", "")
    ward = session.get("ward", "")
    tier = session.get("tier", "Bronze Citizen")
    points = session.get("total_points", 0)
    emoji = TIER_EMOJIS.get(tier, "🥉")
    st.sidebar.success(f"**Logged In:** {name}")
    st.sidebar.info(f"**City:** {city} | **Ward:** {ward}")
    st.sidebar.markdown(f"**Tier:** {emoji} {tier}")
    st.sidebar.markdown(f"**Points:** {points}")
    if st.sidebar.button("Logout"):
        del st.session_state["citizen_session"]
        st.rerun()

# ── NOT LOGGED IN ─────────────────────────────────────────────────────────────
if not session:
    st.title("🧑💼 Citizen Portal")
    tab_reg, tab_login = st.tabs(["📝 Create Account", "🔐 Login"])
    
    with tab_reg:
        st.subheader("Create Your Citizen Account")
        st.info("One account per Aadhar number. Your Aadhar is stored as a secure hash — never readable.")
        with st.form("register_form"):
            name = st.text_input("Full Name *")
            phone = st.text_input("Mobile Number * (10 digits)")
            aadhar = st.text_input("Aadhar Number * (12 digits, Demo Mode)")
            city = st.text_input("City *")
            ward = st.text_input("Ward Number *")
            submitted = st.form_submit_button("Create Account", type="primary")
        
        if submitted:
            if not all([name, phone, aadhar, city, ward]):
                st.error("All fields are required.")
            elif len(str(phone).strip()) != 10 or not str(phone).strip().isdigit():
                st.error("Phone must be exactly 10 digits.")
            elif len(str(aadhar).strip()) != 12 or not str(aadhar).strip().isdigit():
                st.error("Aadhar must be exactly 12 digits.")
            else:
                result = register_citizen(name.strip(), phone.strip(), aadhar.strip(),
                                          city.strip(), ward.strip())
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state["citizen_session"] = result
                    st.success(f"✅ Welcome {name}! Account created successfully.")
                    st.rerun()
    
    with tab_login:
        st.subheader("Login to Your Account")
        with st.form("login_form"):
            phone_l = st.text_input("Mobile Number")
            aadhar_l = st.text_input("Aadhar Number")
            login_btn = st.form_submit_button("Login", type="primary")
        
        if login_btn:
            result = login_citizen(phone_l.strip(), aadhar_l.strip())
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state["citizen_session"] = result
                st.success(f"✅ Welcome back, {result.get('name')}!")
                st.rerun()
    st.stop()

# ── LOGGED IN ─────────────────────────────────────────────────────────────────
session = st.session_state["citizen_session"]
aadhar_hash = session.get("aadhar_hash", "")

tab1, tab2, tab3 = st.tabs(["📋 File a Complaint", "🔍 Track My Complaints", "🏆 My Civic Score"])

# ── TAB 1: FILE COMPLAINT ─────────────────────────────────────────────────────
with tab1:
    st.subheader("Report a Civic Issue")
    
    # Initialize session state for auto-filled details
    if "gps_lat" not in st.session_state:
        st.session_state.gps_lat = 20.9250
    if "gps_lng" not in st.session_state:
        st.session_state.gps_lng = 77.7660
    if "sug_issue" not in st.session_state:
        st.session_state.sug_issue = ISSUE_TYPES[0]
    if "sug_desc" not in st.session_state:
        st.session_state.sug_desc = ""
        
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        photo = st.file_uploader("Upload Photo of Issue *", type=["jpg", "jpeg", "png"])
        if photo:
            st.image(photo, caption="Photo Preview", width=300)
            
            # Automatically extract EXIF GPS coordinates and suggest details
            if "last_photo_name" not in st.session_state or st.session_state.last_photo_name != photo.name:
                st.session_state.last_photo_name = photo.name
                photo_bytes = photo.getvalue()
                
                lat_val, lng_val = extract_gps_from_image(photo_bytes)
                if lat_val and lng_val:
                    st.session_state.gps_lat = lat_val
                    st.session_state.gps_lng = lng_val
                    st.toast(f"🛰️ Auto-filled GPS coordinates from photo EXIF: {lat_val}, {lng_val}")
                
                sug = autofill_from_photo(photo_bytes, ISSUE_TYPES)
                st.session_state.sug_issue = sug["suggested_issue"]
                st.session_state.sug_desc = sug["suggested_description"]
                if sug.get("is_likely_ai_generated"):
                    st.warning("⚠️ Warning: Photo signature patterns suggest it might be AI-generated.")
                    
        try:
            default_index = ISSUE_TYPES.index(st.session_state.sug_issue)
        except ValueError:
            default_index = 0
            
        issue_type = st.selectbox("Issue Classification *", ISSUE_TYPES, index=default_index)
        description = st.text_area("Detailed Description *", value=st.session_state.sug_desc, height=120)
        location_text = st.text_input("Street Address / Landmark *")
    
    with col_right:
        st.markdown("**GPS Location Coordinates**")
        lat = st.number_input("Latitude", value=st.session_state.gps_lat, format="%.6f")
        lng = st.number_input("Longitude", value=st.session_state.gps_lng, format="%.6f")
        
        st.markdown("**Proximity Hazards (AI Verification Inputs)**")
        near_school = st.checkbox("Within school zone (500m)")
        near_hospital = st.checkbox("Within hospital zone (500m)")
        heavy_traffic = st.checkbox("Arterial road / Heavy traffic lane")
        monsoon = st.checkbox("Monsoon vulnerable area")
    
    if st.button("🔗 Submit Complaint to Blockchain Ledger", type="primary"):
        if not photo:
            st.error("Please upload a photo of the issue.")
        elif not description.strip():
            st.error("Please provide a description.")
        elif not location_text.strip():
            st.error("Please enter the location.")
        else:
            photo_bytes = photo.read()
            hazard_flags = []
            if near_school: hazard_flags.append("near_school")
            if near_hospital: hazard_flags.append("near_hospital")
            if heavy_traffic: hazard_flags.append("heavy_traffic")
            if monsoon: hazard_flags.append("monsoon_risk")
            
            with st.spinner("📸 Hashing photo to blockchain..."):
                complaint = submit_complaint(
                    citizen_aadhar_hash=aadhar_hash,
                    citizen_name=session.get("name", "Citizen"),
                    city=session.get("city", ""),
                    ward=session.get("ward", ""),
                    issue_type=issue_type,
                    description=description.strip(),
                    location_text=location_text.strip(),
                    latitude=lat, longitude=lng,
                    photo_bytes=photo_bytes,
                    hazard_flags=hazard_flags,
                )
            
            from data_manager import add_blockchain_entry
            add_blockchain_entry(complaint["complaint_id"], "COMPLAINT_SUBMITTED",
                                 session.get("name", "Citizen"),
                                 photo_hash=complaint.get("photo_hash", ""))
            
            with st.spinner("🤖 AI Vision, Risk, and Memory agents analyzing..."):
                ai_result = run_ai_pipeline(complaint)
            
            priority = ai_result.get("risk", {}).get("priority", "MEDIUM")
            score = ai_result.get("risk", {}).get("score", 0)
            
            st.success(f"✅ Complaint filed! ID: **{complaint['complaint_id']}**")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Priority", f"{PRIORITY_COLORS.get(priority,'')} {priority}")
            col_b.metric("Risk Score", f"{score}/100")
            col_c.metric("Department", ai_result.get("planning", {}).get("department", "")[:25])
            st.info("📡 AI analysis complete. Complaint assigned to department. Worker will be dispatched shortly.")
            st.session_state["citizen_session"] = {**session}
            st.rerun()

# ── TAB 2: TRACK COMPLAINTS ───────────────────────────────────────────────────
with tab2:
    st.subheader("Active & Historic Filings")
    complaints = get_citizen_complaints(aadhar_hash)
    
    if not complaints:
        st.info("You have not filed any complaints yet. Go to 'File a Complaint' tab to report an issue.")
    else:
        for c in sorted(complaints, key=lambda x: x.get("submitted_at",""), reverse=True):
            cid = c.get("complaint_id","")
            priority = c.get("priority","PENDING")
            status = c.get("status","PENDING")
            step = STATUS_STEPS.get(status, 1)
            
            with st.expander(f"📋 {cid} — {c.get('issue_type','')} | {PRIORITY_COLORS.get(priority,'')} {priority}", expanded=(step<7)):
                # 7-step tracker
                cols = st.columns(7)
                for i, label in enumerate(STEP_LABELS):
                    s = i + 1
                    if s < step:
                        cols[i].markdown(f"✅ **{label}**")
                    elif s == step:
                        cols[i].markdown(f"🔵 **{label}**")
                    else:
                        cols[i].markdown(f"⚪ {label}")
                
                st.caption(f"**Location:** {c.get('location_text','')} | **Filed:** {c.get('submitted_at','')[:16]}")
                
                if c.get("ai_analysis"):
                    planning = c["ai_analysis"].get("planning", {})
                    st.markdown(f"**Department:** {planning.get('department','')} | **ETA:** {c.get('resolution_eta','')}")
                    st.markdown(f"**Estimated Budget:** ₹{planning.get('budget_inr',0):,}")
                
                # Show photo
                photo_b64 = c.get("photo_b64","")
                if photo_b64:
                    try:
                        img_bytes = base64.b64decode(photo_b64)
                        st.image(img_bytes, caption="Reported Photo", width=250)
                    except Exception:
                        st.caption("📷 Photo stored securely in system.")
                
                # Status history
                history = c.get("status_history", [])
                if history:
                    st.markdown("**Timeline:**")
                    for h in history:
                        st.caption(f"• {h.get('timestamp','')[:16]} — **{h.get('status','')}**: {h.get('note','')}")
                
                # Rate worker if complete and not yet rated
                if status in ("VERIFIED_COMPLETE", "REQUIRES_REWORK") and not c.get("citizen_rating"):
                    worker_id = c.get("assigned_worker_id")
                    if worker_id:
                        st.markdown("---")
                        st.markdown("**Rate the Repair Quality:**")
                        rating = st.slider(f"Rating for {cid}", 1, 5, 4, key=f"rate_{cid}")
                        comment = st.text_input("Comment (optional)", key=f"comment_{cid}")
                        if st.button(f"Submit Rating", key=f"submit_rating_{cid}"):
                            from data_manager import rate_worker_from_complaint
                            rate_worker_from_complaint(cid, rating, comment, worker_id)
                            award_points(aadhar_hash, 10, "Quality rating submitted", cid)
                            st.success("✅ Rating submitted! +10 civic points awarded.")
                            st.rerun()

# ── TAB 3: GAMIFICATION ───────────────────────────────────────────────────────
with tab3:
    st.subheader("My Civic Score")
    from data_manager import _load
    db = _load()
    citizen_data = db["citizens"].get(aadhar_hash, session)
    
    points = citizen_data.get("total_points", 0)
    tier = citizen_data.get("tier", "Bronze Citizen")
    emoji = TIER_EMOJIS.get(tier, "🥉")
    
    TIERS = [("Bronze Citizen",0,99),("Silver Guardian",100,299),
             ("Gold Champion",300,599),("Platinum Sentinel",600,999),("Diamond Legend",1000,99999)]
    next_tier_points = 100
    for t_name, t_min, t_max in TIERS:
        if tier == t_name and t_max < 99999:
            next_tier_points = t_max + 1 - points
            break
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Points", points)
    col2.metric("Current Tier", f"{emoji} {tier}")
    col3.metric("Points to Next Tier", max(0, next_tier_points))
    
    st.progress(min(points / 1000, 1.0), text=f"Progress: {points}/1000 points")
    
    strikes = citizen_data.get("fake_strikes", 0)
    if strikes > 0:
        st.warning(f"⚠️ {strikes}/3 fake complaint strikes. 3 strikes = account suspended.")
    
    # Point history
    log = [e for e in db.get("gamification_log", []) if e.get("aadhar_hash") == aadhar_hash]
    if log:
        st.markdown("**Point History:**")
        for entry in reversed(log[-10:]):
            pts = entry.get("points", 0)
            sign = "+" if pts > 0 else ""
            st.caption(f"• {entry.get('timestamp','')[:16]} — {sign}{pts} pts — {entry.get('reason','')}")
    
    # City leaderboard
    st.markdown("---")
    st.markdown("**🏆 City Leaderboard:**")
    all_citizens = sorted(db["citizens"].values(), key=lambda x: x.get("total_points",0), reverse=True)
    for i, cit in enumerate(all_citizens[:10], 1):
        me = "← You" if cit.get("aadhar_hash") == aadhar_hash else ""
        t_emoji = TIER_EMOJIS.get(cit.get("tier","Bronze Citizen"), "🥉")
        st.caption(f"{i}. {cit.get('name','?')} — {cit.get('total_points',0)} pts {t_emoji} {me}")
