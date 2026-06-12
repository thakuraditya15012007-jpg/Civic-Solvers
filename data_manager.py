"""
data_manager.py — Single source of truth. All data in data/civic_data.json.
No GCP. No Firestore. No cloud. Works 100% offline.
"""
import json, os, uuid, hashlib, threading
from datetime import datetime, timezone

DATA_FILE = "data/civic_data.json"
_lock = threading.Lock()

def _load() -> dict:
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(DATA_FILE):
        empty = {
            "citizens": {}, "workers": {}, "authorities": {},
            "complaints": {}, "blockchain": [],
            "management_complaints": {}, "gamification_log": []
        }
        with open(DATA_FILE, "w") as f:
            json.dump(empty, f, indent=2)
        return empty
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {
            "citizens": {}, "workers": {}, "authorities": {},
            "complaints": {}, "blockchain": [],
            "management_complaints": {}, "gamification_log": []
        }

def _save(data: dict):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def generate_id(prefix="CS") -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

def hash_text(text: str) -> str:
    return hashlib.sha256(str(text).encode()).hexdigest()

def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

# ── CITIZEN ──────────────────────────────────────────────────────────────────

def register_citizen(name, phone, aadhar, city, ward) -> dict:
    with _lock:
        db = _load()
        phone_hash = hash_text(phone)
        aadhar_hash = hash_text(aadhar)
        if any(c.get("phone_hash") == phone_hash for c in db["citizens"].values()):
            return {"error": "Phone number already registered."}
        if aadhar_hash in db["citizens"]:
            return {"error": "Aadhar number already registered. One citizen = one account."}
        citizen = {
            "aadhar_hash": aadhar_hash, "phone_hash": phone_hash,
            "name": name, "city": city, "ward": ward,
            "registered_at": now_iso(), "total_points": 0,
            "tier": "Bronze Citizen", "fake_strikes": 0, "active": True,
            "phone_display": "******" + str(phone)[-4:],
        }
        db["citizens"][aadhar_hash] = citizen
        _save(db)
        return citizen

def login_citizen(phone, aadhar) -> dict:
    db = _load()
    phone_hash = hash_text(phone)
    aadhar_hash = hash_text(aadhar)
    c = db["citizens"].get(aadhar_hash)
    if not c:
        return {"error": "No account found with this Aadhar number."}
    if c.get("phone_hash") != phone_hash:
        return {"error": "Phone number does not match."}
    if not c.get("active", True):
        return {"error": "Account suspended due to fake complaint strikes."}
    return c

def get_citizen_complaints(aadhar_hash) -> list:
    db = _load()
    return [c for c in db["complaints"].values() if c.get("citizen_aadhar_hash") == aadhar_hash]

def award_points(aadhar_hash, points, reason, complaint_id="") -> dict:
    with _lock:
        db = _load()
        citizen = db["citizens"].get(aadhar_hash)
        if not citizen:
            return {}
        citizen["total_points"] = citizen.get("total_points", 0) + points
        total = citizen["total_points"]
        if total >= 1000:
            citizen["tier"] = "Diamond Legend"
        elif total >= 600:
            citizen["tier"] = "Platinum Sentinel"
        elif total >= 300:
            citizen["tier"] = "Gold Champion"
        elif total >= 100:
            citizen["tier"] = "Silver Guardian"
        else:
            citizen["tier"] = "Bronze Citizen"
        db["citizens"][aadhar_hash] = citizen
        db["gamification_log"].append({
            "aadhar_hash": aadhar_hash, "points": points,
            "reason": reason, "complaint_id": complaint_id,
            "timestamp": now_iso()
        })
        _save(db)
        return citizen

# ── WORKER ───────────────────────────────────────────────────────────────────

def register_worker(name, worker_id, password, city, skills) -> dict:
    with _lock:
        db = _load()
        if worker_id in db["workers"]:
            return {"error": f"Worker ID '{worker_id}' already taken. Choose a different ID."}
        worker = {
            "worker_id": worker_id, "name": name,
            "password_hash": hash_text(password),
            "city": city, "skills": skills,
            "registered_at": now_iso(), "active": True,
            "avg_rating": 0.0, "total_ratings": 0,
            "rating_sum": 0, "completed_jobs": 0,
            "performance_flag": "STANDARD",
        }
        db["workers"][worker_id] = worker
        _save(db)
        return worker

def login_worker(worker_id, password) -> dict:
    db = _load()
    w = db["workers"].get(worker_id)
    if not w:
        return {"error": "Worker ID not found."}
    if w.get("password_hash") != hash_text(password):
        return {"error": "Incorrect password."}
    return w

def get_worker_jobs(worker_id) -> list:
    db = _load()
    return [c for c in db["complaints"].values()
            if c.get("assigned_worker_id") == worker_id
            and c.get("status") not in ["CLOSED", "REJECTED", "FAKE_DETECTED"]]

def get_all_workers() -> list:
    db = _load()
    return list(db["workers"].values())

# ── AUTHORITY ─────────────────────────────────────────────────────────────────

def register_authority(username, password, department, city) -> dict:
    with _lock:
        db = _load()
        if username in db["authorities"]:
            return {"error": "Username already taken."}
        authority = {
            "username": username, "password_hash": hash_text(password),
            "department": department, "city": city,
            "registered_at": now_iso(),
        }
        db["authorities"][username] = authority
        _save(db)
        return authority

def login_authority(username, password) -> dict:
    db = _load()
    # Check registered authorities
    a = db["authorities"].get(username)
    if a and a.get("password_hash") == hash_text(password):
        return a
    # Default admin account always works
    if username == "authority" and password == "authority123":
        return {"username": "authority", "department": "General Administration", "city": "All Cities"}
    return {"error": "Invalid username or password."}

def get_all_complaints() -> list:
    db = _load()
    return list(db["complaints"].values())

def get_management_complaints() -> list:
    db = _load()
    return list(db["management_complaints"].values())

# ── COMPLAINT ─────────────────────────────────────────────────────────────────

def submit_complaint(citizen_aadhar_hash, citizen_name, city, ward,
                     issue_type, description, location_text,
                     latitude, longitude, photo_bytes, hazard_flags) -> dict:
    with _lock:
        db = _load()
        cid = generate_id("CS")
        photo_hash = hash_bytes(photo_bytes) if photo_bytes else ""
        
        # Store photo as base64 string so st.image() can display it directly
        import base64
        photo_b64 = base64.b64encode(photo_bytes).decode() if photo_bytes else ""
        
        complaint = {
            "complaint_id": cid,
            "citizen_aadhar_hash": citizen_aadhar_hash,
            "citizen_name": citizen_name,
            "city": city, "ward": ward,
            "issue_type": issue_type,
            "description": description,
            "location_text": location_text,
            "latitude": float(latitude or 0),
            "longitude": float(longitude or 0),
            "photo_b64": photo_b64,
            "photo_hash": photo_hash,
            "completion_photo_b64": "",
            "completion_photo_hash": "",
            "submitted_at": now_iso(),
            "status": "PENDING",
            "risk_score": 0,
            "priority": "PENDING",
            "assigned_department": "",
            "assigned_worker_id": None,
            "resolution_eta": "AI analyzing...",
            "ai_analysis": {},
            "drone_verdict": None,
            "citizen_rating": None,
            "management_complaint_filed": False,
            "is_recurring": False,
            "hazard_flags": hazard_flags,
            "status_history": [{
                "status": "PENDING",
                "timestamp": now_iso(),
                "note": "Complaint submitted. AI analysis starting.",
                "actor": citizen_name,
            }],
        }
        db["complaints"][cid] = complaint
        _save(db)
    return complaint

def update_complaint(complaint_id, updates: dict, status_note="", actor="SYSTEM") -> bool:
    with _lock:
        db = _load()
        c = db["complaints"].get(complaint_id)
        if not c:
            return False
        new_status = updates.get("status")
        if new_status and new_status != c.get("status"):
            history = c.get("status_history", [])
            history.append({
                "status": new_status,
                "timestamp": now_iso(),
                "note": status_note or f"Status changed to {new_status}",
                "actor": actor,
            })
            updates["status_history"] = history
        c.update(updates)
        db["complaints"][complaint_id] = c
        _save(db)
    return True

def rate_worker_from_complaint(complaint_id, rating, comment, worker_id) -> bool:
    with _lock:
        db = _load()
        c = db["complaints"].get(complaint_id)
        if not c:
            return False
        c["citizen_rating"] = rating
        c["citizen_rating_comment"] = comment
        c["status"] = "CITIZEN_RATED"
        db["complaints"][complaint_id] = c
        
        w = db["workers"].get(worker_id)
        if w:
            total = w.get("total_ratings", 0) + 1
            rating_sum = w.get("rating_sum", 0) + rating
            avg = round(rating_sum / total, 2)
            w["total_ratings"] = total
            w["rating_sum"] = rating_sum
            w["avg_rating"] = avg
            w["completed_jobs"] = w.get("completed_jobs", 0) + 1
            if total >= 5 and avg < 2.5:
                w["performance_flag"] = "REVIEW_REQUIRED"
            elif avg >= 4.0:
                w["performance_flag"] = "PREFERRED"
            db["workers"][worker_id] = w
        _save(db)
    return True

# ── BLOCKCHAIN ────────────────────────────────────────────────────────────────

def add_blockchain_entry(complaint_id, event, actor, photo_hash="", metadata=None) -> dict:
    with _lock:
        db = _load()
        chain = db.get("blockchain", [])
        
        # Get previous hash from last block
        if chain:
            last = chain[-1]
            stable = {k: last.get(k, "") for k in
                      ["block_id", "complaint_id", "event", "actor", "timestamp", "photo_hash"]}
            prev_hash = hash_text(json.dumps(stable, sort_keys=True))
        else:
            prev_hash = "0" * 64
        
        block = {
            "block_id": str(uuid.uuid4()),
            "complaint_id": complaint_id,
            "event": event,
            "actor": actor,
            "photo_hash": photo_hash,
            "metadata": metadata or {},
            "timestamp": now_iso(),
            "prev_hash": prev_hash,
        }
        chain.append(block)
        db["blockchain"] = chain
        _save(db)
    return block

def verify_blockchain() -> dict:
    db = _load()
    chain = db.get("blockchain", [])
    if not chain:
        return {"total": 0, "intact": True, "broken": [],
                "message": "Chain empty — no entries yet."}
    broken = []
    for i in range(1, len(chain)):
        prev = chain[i - 1]
        stable = {k: prev.get(k, "") for k in
                  ["block_id", "complaint_id", "event", "actor", "timestamp", "photo_hash"]}
        expected = hash_text(json.dumps(stable, sort_keys=True))
        actual = chain[i].get("prev_hash", "")
        if expected != actual:
            broken.append({
                "index": i, "event": chain[i].get("event"),
                "complaint_id": chain[i].get("complaint_id"),
            })
    return {
        "total": len(chain), "intact": len(broken) == 0, "broken": broken,
        "message": (f"✅ All {len(chain)} entries verified — chain intact."
                    if not broken else f"🚨 {len(broken)} broken links detected.")
    }

# ── DRONE AUTONOMOUS PATROL ───────────────────────────────────────────────────

def drone_patrol_and_escalate() -> dict:
    """
    Autonomous drone patrol. Runs automatically.
    Scans all complaints and files management complaints for violations.
    No human triggers this. Called on Authority dashboard load.
    """
    from datetime import timedelta
    import dateutil.parser
    
    SLA_HOURS = {"CRITICAL": 24, "HIGH": 72, "MEDIUM": 168, "LOW": 336}
    violations_found = 0
    escalated = []
    
    with _lock:
        db = _load()
        complaints = db["complaints"]
        
        for cid, c in complaints.items():
            status = c.get("status", "")
            priority = c.get("priority", "LOW")
            worker_id = c.get("assigned_worker_id")
            
            try:
                assigned_at_str = None
                for h in c.get("status_history", []):
                    if h.get("status") == "ASSIGNED":
                        assigned_at_str = h.get("timestamp")
                        break
                
                if not assigned_at_str:
                    continue
                    
                assigned_at = dateutil.parser.parse(assigned_at_str)
                hours_elapsed = (datetime.now(timezone.utc) - assigned_at).total_seconds() / 3600
                sla_limit = SLA_HOURS.get(priority, 168)
                
                # Violation 1: Worker didn't accept within 24 hours
                if status == "ASSIGNED" and hours_elapsed > 24 and not c.get("accepted_at"):
                    mc_id = generate_id("MC")
                    mc = {
                        "management_complaint_id": mc_id,
                        "complaint_id": cid,
                        "worker_id": worker_id or "UNASSIGNED",
                        "violation": "NON_ACCEPTANCE",
                        "note": f"Worker did not accept complaint within 24 hours. Elapsed: {hours_elapsed:.1f}h",
                        "filed_by": "DRONE_AUTONOMOUS_SYSTEM",
                        "filed_at": now_iso(),
                        "status": "OPEN",
                    }
                    db["management_complaints"][mc_id] = mc
                    c["status"] = "ESCALATED"
                    c["management_complaint_filed"] = True
                    complaints[cid] = c
                    violations_found += 1
                    escalated.append(mc_id)
                    add_blockchain_entry(cid, "MANAGEMENT_COMPLAINT_FILED",
                                        "DRONE_AUTONOMOUS_SYSTEM",
                                        metadata={"violation": "NON_ACCEPTANCE"})
                
                # Violation 2: SLA breached
                elif status in ["ACCEPTED", "IN_PROGRESS"] and hours_elapsed > sla_limit:
                    mc_id = generate_id("MC")
                    mc = {
                        "management_complaint_id": mc_id,
                        "complaint_id": cid,
                        "worker_id": worker_id or "UNKNOWN",
                        "violation": "SLA_BREACH",
                        "note": f"SLA of {sla_limit}h breached. Elapsed: {hours_elapsed:.1f}h. Priority: {priority}",
                        "filed_by": "DRONE_AUTONOMOUS_SYSTEM",
                        "filed_at": now_iso(),
                        "status": "OPEN",
                    }
                    db["management_complaints"][mc_id] = mc
                    c["status"] = "ESCALATED"
                    c["management_complaint_filed"] = True
                    complaints[cid] = c
                    violations_found += 1
                    escalated.append(mc_id)
                    add_blockchain_entry(cid, "MANAGEMENT_COMPLAINT_FILED",
                                        "DRONE_AUTONOMOUS_SYSTEM",
                                        metadata={"violation": "SLA_BREACH"})
            except Exception:
                continue
        
        db["complaints"] = complaints
        _save(db)
    
    return {"violations_found": violations_found, "escalated": escalated,
            "patrol_at": now_iso()}
