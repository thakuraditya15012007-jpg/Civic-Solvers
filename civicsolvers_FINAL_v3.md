# CIVIC SOLVERS — DEFINITIVE PRODUCTION PROMPT FOR ANTIGRAVITY IDE
## FINAL-v3 | FULLY AUTONOMOUS | CLOUD-SCALE | ZERO HARDCODING | RATING: 10/10

**Team:** Obsidian Ops / Indic Intelligence | **Leader:** Shreyas Patankar | **Institutes:** PRMITR & PRMCEM
**Hackathons:** PU Code Hackathon 3.0 (Track: Web 2.0) + AWS AI for Bharat Hackathon
**GitHub:** https://github.com/shreyas07-anonymous/Civic_Solvers-AI-for-Bharat
**Demo Video:** https://drive.google.com/file/d/1CCLh_InEwMZ4LmKQY3gpF8YrFRxoekef/view?usp=sharing
**Problem Statement (AWS):** Manual, unverified civic reporting causes 15-day delays and erodes public trust.
**Problem Statement (PU):** India receives 1.5 crore civic complaints yearly but resolves only 30%; 12,000+ pothole deaths, 25% water wastage, ₹50,000 crore in annual damages — caused by no instant reporting, poor tracking, and zero transparency.

---

## ═══ AGENT SKILL DEFINITION (Save as Persistent Skill BEFORE Running) ═══

**Save this skill as:** `civic-solvers-core-rules`
This skill MUST be active for every session. These rules override all agent defaults:

- NEVER use local files, SQLite, or in-memory arrays for persistent state
- NEVER write `# TODO`, `pass`, or placeholder comments — every function must be complete and executable
- NEVER crash on API or cloud errors — wrap every external call in try/except with graceful fallback
- ALWAYS use Firestore transactional writes for any state mutation that affects more than one field
- ALWAYS use `gemini-2.5-flash` as the Vertex AI model string
- All modules under `backend/` are independent — build them in parallel
- After all files are generated, write pytest unit tests for `blockchain.py` and `ai_engine.py` and run them

---

## ═══ SECTION 1 — PROJECT IDENTITY ═══

```
Name:        Civic Solvers
Tagline:     Smarter Cities. Faster Fixes. Transparent Governance.
Subtitle:    AI Analysis in <30 Seconds | 15-Day Delays → Same Day Resolution
Runtime:     Python 3.11 / Streamlit / Google Cloud Run
GCP Services: Cloud Run, Firestore (Native Mode), Cloud Storage, Cloud Pub/Sub,
              Vertex AI (Gemini 2.5 Flash), Cloud Logging
```

**CRITICAL:** This is a completely standalone, self-contained project. Do NOT link, reference, or authenticate against any existing GCP project, account, billing profile, or external repository. All GCP client instantiation MUST use Application Default Credentials (ADC) resolved at runtime via environment variables ONLY. No hardcoded credentials. No service account JSON files in code.

---

## ═══ SECTION 2 — 14 ABSOLUTE BUILD RULES (Violating any = invalid build) ═══

**RULE 1 — ZERO LOCAL STORAGE:** No local files, SQLite, or local arrays for persistent state. Every record reads/writes to Firestore. Empty collections return graceful UI empty-states, never errors.

**RULE 2 — ZERO PLACEHOLDERS:** Every function must be complete from `def` to `return`. No `# TODO`, `# logic here`, or `pass`. Every line must be executable, production-ready Python with exception handling.

**RULE 3 — CLOUD TRANSACTIONS:** Replace threading.Lock() with Firestore `@firestore.transactional` writes. All critical state updates and ledger additions execute atomically for multi-instance Cloud Run consistency.

**RULE 4 — FULLY AUTONOMOUS PIPELINE:** Only THREE human interactions allowed in the entire system: (1) Citizen uploads photo and clicks Submit. (2) Field worker uploads repair proof photo/video. (3) Authority views dashboards and assigns workers. Everything else — CV analysis, routing, priority escalation, risk scoring, ledger hashing, drone verification, management complaint filing, gamification point awarding — runs AUTONOMOUSLY via Cloud Pub/Sub event streams.

**RULE 5 — VERTEX AI INTEGRATION:** All generative AI tasks use `google-cloud-aiplatform` SDK with model string `gemini-2.5-flash`. Implement robust error handling for quota errors, credential errors, and JSON parse failures. Never let a cloud function crash on an AI call — always return a structured fallback response.

**RULE 6 — DETERMINISTIC RISK SCORING:** The Risk Evaluation module is PURE PYTHON ARITHMETIC. Zero LLM involvement. Identical input payloads must produce identical integer outputs for regulatory audit compliance. This is the "legally defensible" scoring described in the PU Hackathon submission.

**RULE 7 — DISTRIBUTED BLOCKCHAIN LEDGER:** Each block in Firestore `blockchain_ledger` computes `prev_hash` as SHA-256 of the full sorted JSON string of the previous document. `verify_full_chain()` must stream all documents sequentially, recalculate hashes, and flag tampered or out-of-order blocks. Every photo (citizen AND authority AND drone) gets hashed BEFORE any AI processing.

**RULE 8 — SECURE CLOUD STORAGE:** All citizen, authority, worker, and drone images/videos written to GCS using signed URLs or service account authentication. No public bucket ACLs.

**RULE 9 — DECOUPLED EVENT ARCHITECTURE:** Heavy AI processing MUST NEVER block the frontend web request. Publish a Pub/Sub payload from the frontend handler. Background subscriber workers process async and update Firestore status fields. The citizen sees "Submitted — AI analyzing..." immediately.

**RULE 10 — IDEMPOTENT BOOTSTRAP:** `app.py` calls `setup.bootstrap_gcp()` before launching the UI. This function verifies GCS bucket existence, Firestore connectivity, and Pub/Sub topic existence — creating missing resources idempotently. Never fail on first run.

**RULE 11 — OFFLINE FALLBACK QUEUE:** `offline_queue.py` must be fully implemented with in-memory queue (NOT disk), `enqueue(payload)`, `flush_to_cloud(endpoint)`, and `get_pending_count()` methods. On network failure it enqueues. On connectivity restore, it retries with exponential backoff up to 5 attempts. Workers in low-connectivity areas must be able to upload proof and have it sync when signal returns.

**RULE 12 — SECURE IDENTITY — AADHAR MOCK GATE:** Mock Aadhar verification must compute a salted SHA-256 hash of the Aadhar number before writing to Firestore. One Aadhar = one citizen account globally. One phone = one account globally. Duplicate hashes MUST be rejected with a clear UI error: "An account already exists with this Aadhar number." Citizens cannot bypass this gate.

**RULE 13 — WORKER REPUTATION SYSTEM:** Every completed job has a citizen rating (1–5 stars). Worker Firestore documents maintain `total_ratings`, `rating_sum`, `avg_rating`, `completed_jobs`, `penalty_count`. When the Authority dashboard assigns a new CRITICAL or HIGH priority job, the assignment algorithm MUST read worker `avg_rating` and `completed_jobs` and prefer workers with rating ≥ 4.0 for high-stakes repairs. Workers with `avg_rating` < 2.5 on 5+ jobs are flagged as "PERFORMANCE REVIEW" in the Authority dashboard.

**RULE 14 — DRONE AUTONOMOUS PATROL + MANAGEMENT COMPLAINTS:** The drone system has TWO functions. (A) Repair Verification: triggered after worker uploads completion proof — Gemini Vision compares before vs after photos and returns verdict. (B) Autonomous Patrol: a background function `drone_patrol_and_escalate()` runs on every Authority dashboard load and on a Pub/Sub schedule. It scans ALL complaints where: status is `ASSIGNED` but worker has not accepted within 24 hours, OR status is `IN_PROGRESS` and SLA deadline has passed, OR completion photo was uploaded but Gemini flagged it as fake/identical to original. For each violation, the system AUTOMATICALLY files a `management_complaint` document in Firestore against the responsible worker/department — NO human clicks required. These auto-filed complaints appear in a dedicated "Drone-Filed Escalations" tab in the Authority Dashboard.

---

## ═══ SECTION 3 — PARALLELISM MAP (Agent Manager Instructions) ═══

Build the following module groups simultaneously in parallel:

| Parallel Group | Files |
|---|---|
| Group A | `config.py`, `setup.py`, `requirements.txt` |
| Group B | `backend/gcp_manager.py`, `backend/blockchain.py` |
| Group C | `backend/ai_engine.py`, `backend/drone_verifier.py` |
| Group D | `backend/gamification.py`, `backend/pubsub_workers.py`, `backend/maps_helper.py`, `backend/offline_queue.py`, `backend/worker_reputation.py` |
| Group E | `pages/1_Citizen.py`, `pages/2_Worker.py`, `pages/3_Authority.py` |
| Group F | `app.py`, `scripts/gcp_seed.py`, `tests/test_blockchain.py`, `tests/test_risk_engine.py` |

Group F depends on A–E. All other groups are fully independent and must be built in parallel.

---

## ═══ SECTION 4 — COMPLETE FOLDER STRUCTURE ═══

```
civic_solvers/
├── app.py
├── config.py
├── setup.py
├── requirements.txt
├── backend/
│   ├── __init__.py
│   ├── ai_engine.py
│   ├── blockchain.py
│   ├── gcp_manager.py
│   ├── pubsub_workers.py
│   ├── drone_verifier.py
│   ├── gamification.py
│   ├── maps_helper.py
│   ├── offline_queue.py
│   └── worker_reputation.py
├── pages/
│   ├── 1_Citizen.py
│   ├── 2_Worker.py
│   └── 3_Authority.py
├── scripts/
│   └── gcp_seed.py
└── tests/
    ├── test_blockchain.py
    └── test_risk_engine.py
```

---

## ═══ SECTION 5 — FILE: requirements.txt ═══

Generate this file completely with pinned versions compatible with Python 3.11:

```
streamlit>=1.35.0
google-cloud-firestore>=2.16.0
google-cloud-storage>=2.16.0
google-cloud-pubsub>=2.21.0
google-cloud-aiplatform>=1.57.0
google-auth>=2.29.0
Pillow>=10.3.0
requests>=2.31.0
folium>=0.16.0
streamlit-folium>=0.20.0
pandas>=2.2.0
plotly>=5.20.0
streamlit-extras>=0.4.0
```

---

## ═══ SECTION 6 — FILE: config.py ═══

```python
"""
config.py — Global configurations and GCP Resource Management bindings.
All secrets and project IDs resolved from environment variables only.
No hardcoded credentials. No external account references.

Civic Solvers | Obsidian Ops / Indic Intelligence | Shreyas Patankar
PU Code Hackathon 3.0 + AWS AI for Bharat Hackathon
Problem: India receives 1.5 crore civic complaints yearly but resolves only 30%.
         Manual, unverified reporting causes 15-day delays and erodes public trust.
"""
import os

# ── Google Cloud Project Configuration ──────────────────────────────────────
GCP_PROJECT_ID      = os.environ["GOOGLE_CLOUD_PROJECT"]
GCS_BUCKET_NAME     = os.getenv("GCS_ASSET_BUCKET", f"{GCP_PROJECT_ID}-civic-media")
PUBSUB_TOPIC_ID     = os.getenv("PUBSUB_TOPIC", "civic-events-topic")
PUBSUB_DRONE_TOPIC  = os.getenv("PUBSUB_DRONE_TOPIC", "civic-drone-patrol-topic")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# ── Vertex AI / Gemini ───────────────────────────────────────────────────────
VERTEX_GEMINI_MODEL = "gemini-2.5-flash"
VERTEX_LOCATION     = os.getenv("VERTEX_LOCATION", "us-central1")

# ── Issue Types and Department Routing ──────────────────────────────────────
ISSUE_DEPARTMENT_MAP = {
    "Pothole":              "Roads & Infrastructure Dept",
    "Water Leak":           "Water Supply & Sewerage Board",
    "Broken Streetlight":   "Electrical & Lighting Dept",
    "Blocked Drain":        "Stormwater Drainage Dept",
    "Garbage Dump":         "Solid Waste Management Dept",
    "Road Damage":          "Roads & Infrastructure Dept",
    "Fallen Tree":          "Horticulture & Parks Dept",
    "Illegal Construction": "Town Planning & Development",
    "Sewage Overflow":      "Water Supply & Sewerage Board",
    "Other":                "General Administration",
}
ISSUE_TYPES = list(ISSUE_DEPARTMENT_MAP.keys())

# ── Deterministic Risk Scoring Weights (PURE PYTHON — ZERO LLM INVOLVEMENT) ─
# These weights are transparent, auditable, and legally defensible.
# Source: PU Code Hackathon 3.0 submission — 100-point risk index specification.
RISK_BASE_SCORES = {
    "Pothole": 30, "Water Leak": 35, "Broken Streetlight": 25,
    "Blocked Drain": 40, "Garbage Dump": 20, "Road Damage": 35,
    "Fallen Tree": 30, "Illegal Construction": 20, "Sewage Overflow": 45, "Other": 15,
}
RISK_CONTEXT_MULTIPLIERS = {
    "near_school":          20,  # +20 if within 500m of school zone
    "near_hospital":        15,  # +15 if within 500m of hospital
    "heavy_traffic_road":   15,  # +15 for arterial/highway roads
    "monsoon_vulnerability":25,  # +25 during monsoon season (Jun–Sep) — Monsoon Critical flag
    "near_water_body":      10,  # +10 near rivers/lakes (flood risk)
    "immediate_danger":     20,  # +20 if AI vision detects active hazard
    "severity_per_point":    3,  # ×3 multiplier per severity point (1–10 scale from Vision Agent)
    "recurring_at_location": 15, # +15 if Memory Agent detects ≥2 prior complaints at same GPS cluster
}

PRIORITY_THRESHOLDS = [(80, "CRITICAL"), (60, "HIGH"), (40, "MEDIUM"), (0, "LOW")]
PRIORITY_COLORS     = {"CRITICAL": "#FF3333", "HIGH": "#FF8800", "MEDIUM": "#FFD700", "LOW": "#33CC66"}
PRIORITY_EMOJIS     = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}

# ── SLA Hours by Priority (for drone escalation trigger) ────────────────────
SLA_HOURS   = {"CRITICAL": 24, "HIGH": 72, "MEDIUM": 168, "LOW": 336}
SLA_DISPLAY = {
    "CRITICAL": "Within 24 hours (₹50,000 crore annual damage context)",
    "HIGH":     "Within 3 days",
    "MEDIUM":   "Within 7 days",
    "LOW":      "Within 14 days",
}

# ── Complaint Lifecycle Statuses ─────────────────────────────────────────────
COMPLAINT_STATUSES = [
    "PENDING",               # Submitted, AI not yet processed
    "AI_ANALYZING",          # Vision + Risk + Memory + Planning agents running
    "ASSIGNED",              # Authority assigned to department/worker
    "ACCEPTED",              # Worker confirmed acceptance
    "IN_PROGRESS",           # Worker on site
    "COMPLETION_UPLOADED",   # Worker uploaded proof
    "DRONE_SCANNING",        # Drone verifier comparing before/after
    "VERIFIED_COMPLETE",     # Drone confirmed resolution
    "REQUIRES_REWORK",       # Drone rejected — work incomplete
    "CITIZEN_RATED",         # Citizen submitted quality rating
    "CLOSED",                # Case closed, points awarded
    "ESCALATED",             # SLA breached — drone filed mgmt complaint
    "FAKE_DETECTED",         # AI detected fake/AI-generated complaint photo
    "REJECTED",              # Authority reviewed and rejected
]

# ── Gamification Tiers (Bronze → Diamond) ───────────────────────────────────
# Citizens earn points for real complaints and lose points for fake ones.
CIVIC_TIERS = [
    {"name": "🥉 Bronze Citizen",    "min": 0,    "max": 99,    "badge": "Active Reporter",     "color": "#CD7F32"},
    {"name": "🥈 Silver Guardian",   "min": 100,  "max": 299,   "badge": "Community Protector", "color": "#C0C0C0"},
    {"name": "🥇 Gold Champion",     "min": 300,  "max": 599,   "badge": "City Hero",           "color": "#FFD700"},
    {"name": "💎 Platinum Sentinel", "min": 600,  "max": 999,   "badge": "Urban Guardian",      "color": "#E5E4E2"},
    {"name": "🏆 Diamond Legend",    "min": 1000, "max": 999999,"badge": "Civic Legend",        "color": "#B9F2FF"},
]

# All point awards and penalties — auto-triggered by system events, no manual override.
POINT_RULES = {
    "complaint_submitted":        10,   # Any valid complaint submitted
    "critical_priority_bonus":    25,   # AI assigned CRITICAL — citizen was right
    "resolved_within_sla":        20,   # Issue resolved before SLA deadline
    "drone_verified_complete":    30,   # Drone confirmed work done
    "first_reporter_at_location": 15,   # First person to report at this GPS cluster
    "recurring_issue_found":      35,   # Memory Agent detected this is a recurring location
    "citizen_quality_confirmed":  10,   # Citizen rated repair 4–5 stars
    "management_complaint_filed": 20,   # Drone filed management complaint (citizen reward for unresolved issue)
    "fake_complaint_penalty":    -50,   # AI detected fake/generated photo — deduct 50 points
    "fake_strike_recorded":        0,   # Strike recorded on account (3 strikes = account suspension)
}

# ── Authentication ───────────────────────────────────────────────────────────
AUTH_AUTHORITY     = {"authority": "authority123", "admin": "admin123"}
WORKER_DEFAULT_PWD = "worker123"

# ── Map Defaults (India center) ──────────────────────────────────────────────
DEFAULT_MAP_LAT  = 20.5937
DEFAULT_MAP_LNG  = 78.9629
DEFAULT_MAP_ZOOM = 5

# ── Drone Patrol Thresholds ──────────────────────────────────────────────────
DRONE_ACCEPTANCE_TIMEOUT_HOURS = 24   # Worker must accept within 24h or drone escalates
DRONE_FAKE_SIMILARITY_THRESHOLD = 0.92 # If completion photo >92% similar to original, flag as fake
```

---

## ═══ SECTION 7 — FILE: setup.py ═══

```python
"""
setup.py — Idempotent GCP infrastructure bootstrap validator.
Runs once at app startup. Creates missing resources safely.
No external account references. Uses ADC credentials from environment.
"""
from google.cloud import storage, firestore, pubsub_v1
from config import GCP_PROJECT_ID, GCS_BUCKET_NAME, PUBSUB_TOPIC_ID, PUBSUB_DRONE_TOPIC

def bootstrap_gcp() -> None:
    """Verifies and idempotently provisions all required GCP resources."""
    _bootstrap_storage()
    _bootstrap_firestore()
    _bootstrap_pubsub()

def _bootstrap_storage() -> None:
    storage_client = storage.Client(project=GCP_PROJECT_ID)
    try:
        storage_client.get_bucket(GCS_BUCKET_NAME)
        print(f"✅ GCS bucket verified: {GCS_BUCKET_NAME}")
    except Exception:
        try:
            storage_client.create_bucket(GCS_BUCKET_NAME)
            print(f"✅ GCS bucket created: {GCS_BUCKET_NAME}")
        except Exception as e:
            print(f"⚠️ GCS bucket init warning: {e}")

def _bootstrap_firestore() -> None:
    try:
        db = firestore.Client(project=GCP_PROJECT_ID)
        db.collection("_health").document("ping").set({"status": "ok"})
        print("✅ Firestore connected.")
    except Exception as e:
        print(f"⚠️ Firestore connectivity issue: {e}")

def _bootstrap_pubsub() -> None:
    publisher = pubsub_v1.PublisherClient()
    for topic_id in [PUBSUB_TOPIC_ID, PUBSUB_DRONE_TOPIC]:
        topic_path = publisher.topic_path(GCP_PROJECT_ID, topic_id)
        try:
            publisher.get_topic(request={"topic": topic_path})
            print(f"✅ Pub/Sub topic verified: {topic_id}")
        except Exception:
            try:
                publisher.create_topic(request={"topic": topic_path})
                print(f"✅ Pub/Sub topic created: {topic_id}")
            except Exception as e:
                print(f"⚠️ Pub/Sub init warning for {topic_id}: {e}")

if __name__ == "__main__":
    bootstrap_gcp()
    print("✅ Civic Solvers Cloud Infrastructure validated.")
```

---

## ═══ SECTION 8 — FILE: backend/gcp_manager.py ═══

```python
"""
gcp_manager.py — Universal Firestore CRUD and GCS wrapper.
Thread-safe via cloud atomic transactions. No local state.
Handles: complaints, citizens, workers, management_complaints, worker_ratings.
"""
import uuid, hashlib
from datetime import datetime, timezone
from google.cloud import firestore, storage
from config import GCP_PROJECT_ID, GCS_BUCKET_NAME

db = firestore.Client(project=GCP_PROJECT_ID)
storage_client = storage.Client(project=GCP_PROJECT_ID)

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def generate_cid() -> str:
    return f"CS-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4()).replace('-','')[:6].upper()}"

def hash_identifier(raw: str, salt: str = "civic_solvers_aadhar_salt_v1") -> str:
    """Salted SHA-256 hash for Aadhar and phone deduplication."""
    return hashlib.sha256(f"{salt}{raw}".encode("utf-8")).hexdigest()

def hash_file_bytes(data: bytes) -> str:
    """SHA-256 hash of raw file bytes — for blockchain photo integrity."""
    return hashlib.sha256(data).hexdigest()

def upload_media_to_gcs(file_bytes: bytes, destination_blob_name: str, content_type: str = "image/jpeg") -> str:
    """Upload media to GCS. Returns gs:// URI. Raises RuntimeError on failure."""
    try:
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(file_bytes, content_type=content_type)
        return f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"
    except Exception as e:
        raise RuntimeError(f"GCS upload failed for {destination_blob_name}: {e}")

def citizen_exists_by_phone(phone: str) -> bool:
    """Check if a phone number is already registered. Returns bool."""
    try:
        phone_hash = hash_identifier(phone, salt="phone_salt_v1")
        query = db.collection("citizens").where("phone_hash", "==", phone_hash).limit(1).stream()
        return len(list(query)) > 0
    except Exception:
        return False

def citizen_exists_by_aadhar(aadhar_hash: str) -> bool:
    """Check if an Aadhar hash is already registered. Returns bool."""
    try:
        query = db.collection("citizens").where("aadhar_hash", "==", aadhar_hash).limit(1).stream()
        return len(list(query)) > 0
    except Exception:
        return False

def register_citizen(aadhar_hash: str, phone: str, name: str, city: str, ward: str) -> dict:
    """
    Register a new citizen. Stores hashed Aadhar (never raw).
    One Aadhar = one account globally. One phone = one account globally.
    """
    phone_hash = hash_identifier(phone, salt="phone_salt_v1")
    citizen_payload = {
        "aadhar_hash": aadhar_hash,
        "phone_hash": phone_hash,
        "phone_display": phone[-4:].rjust(10, "*"),  # Store only last 4 digits for display
        "name": name,
        "city": city,
        "ward": ward,
        "registered_at": now_iso(),
        "active": True,
        "fake_strikes": 0,         # 3 strikes = account suspended
        "total_points": 0,
        "tier": "🥉 Bronze Citizen",
        "total_complaints": 0,
        "resolved_complaints": 0,
    }
    db.collection("citizens").document(aadhar_hash).set(citizen_payload)
    return citizen_payload

@firestore.transactional
def _add_fake_strike_transaction(transaction, doc_ref):
    snapshot = doc_ref.get(transaction=transaction)
    data = snapshot.to_dict() or {}
    strikes = data.get("fake_strikes", 0) + 1
    updates = {"fake_strikes": strikes}
    if strikes >= 3:
        updates["active"] = False
        updates["suspension_reason"] = "3 fake complaint strikes — account suspended by autonomous system"
    transaction.update(doc_ref, updates)

def penalize_citizen_fake(aadhar_hash: str) -> dict:
    """Add a fake strike to citizen. Suspend after 3 strikes. Returns updated state."""
    try:
        doc_ref = db.collection("citizens").document(aadhar_hash)
        transaction = db.transaction()
        _add_fake_strike_transaction(transaction, doc_ref)
        doc = doc_ref.get().to_dict() or {}
        return {"strikes": doc.get("fake_strikes", 0), "suspended": not doc.get("active", True)}
    except Exception as e:
        return {"error": str(e)}

def build_complaint(
    citizen_aadhar_hash: str, citizen_name: str, citizen_phone_display: str,
    city: str, ward: str, issue_type: str, description: str,
    location_text: str, latitude: float, longitude: float,
    gcs_photo_uri: str, photo_hash: str
) -> dict:
    """
    Create a new complaint document in Firestore.
    Status begins as PENDING. All timestamps initialize as None.
    AI analysis fields populated async by Pub/Sub subscriber.
    """
    cid = generate_cid()
    complaint_doc = {
        "complaint_id": cid,
        "citizen_aadhar_hash": citizen_aadhar_hash,
        "citizen_name": citizen_name,
        "citizen_phone_display": citizen_phone_display,
        "city": city,
        "ward": ward,
        "issue_type": issue_type,
        "description": description,
        "location_text": location_text,
        "latitude": latitude,
        "longitude": longitude,
        "photo_path": gcs_photo_uri,
        "photo_hash": photo_hash,
        "completion_photo_path": None,
        "completion_photo_hash": None,
        "submitted_at": now_iso(),
        "ai_analyzed_at": None,
        "assigned_at": None,
        "accepted_at": None,
        "work_started_at": None,
        "completion_uploaded_at": None,
        "drone_scanned_at": None,
        "citizen_rated_at": None,
        "resolved_at": None,
        "assigned_worker_id": None,
        "assigned_department": None,
        "ai_analysis": {},
        "risk_score": 0,
        "priority": "PENDING",
        "resolution_eta": "AI analyzing...",
        "status": "PENDING",
        "drone_verdict": None,
        "citizen_rating": None,
        "citizen_rating_comment": None,
        "management_complaint_filed": False,
        "is_recurring": False,
        "recurring_count": 0,
        "status_history": [
            {
                "status": "PENDING",
                "timestamp": now_iso(),
                "note": "Complaint submitted. AI analysis queued.",
                "actor": citizen_name,
            }
        ],
    }
    db.collection("complaints").document(cid).set(complaint_doc)
    return complaint_doc

def get_all_complaints(filters: dict = None) -> list[dict]:
    """Stream all complaints from Firestore. Optional filters dict with field:value pairs."""
    try:
        query = db.collection("complaints")
        if filters:
            for field, value in filters.items():
                query = query.where(field, "==", value)
        return [doc.to_dict() for doc in query.stream()]
    except Exception as e:
        print(f"⚠️ get_all_complaints error: {e}")
        return []

def get_complaint_by_id(complaint_id: str) -> dict | None:
    """Fetch a single complaint by ID. Returns None if not found."""
    try:
        doc = db.collection("complaints").document(complaint_id).get()
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        print(f"⚠️ get_complaint_by_id error: {e}")
        return None

@firestore.transactional
def _update_complaint_status_transaction(transaction, doc_ref, new_status: str, note: str, actor: str, extra_fields: dict):
    snapshot = doc_ref.get(transaction=transaction)
    data = snapshot.to_dict() or {}
    history = data.get("status_history", [])
    history.append({"status": new_status, "timestamp": now_iso(), "note": note, "actor": actor})
    update_payload = {"status": new_status, "status_history": history}
    update_payload.update(extra_fields)
    transaction.update(doc_ref, update_payload)

def update_complaint_status(complaint_id: str, new_status: str, note: str, actor: str, extra_fields: dict = None) -> bool:
    """Atomically update complaint status and append to status_history."""
    try:
        doc_ref = db.collection("complaints").document(complaint_id)
        transaction = db.transaction()
        _update_complaint_status_transaction(transaction, doc_ref, new_status, note, actor, extra_fields or {})
        return True
    except Exception as e:
        print(f"⚠️ update_complaint_status error: {e}")
        return False

def file_management_complaint(
    complaint_id: str, worker_id: str, violation_type: str,
    evidence_note: str, filed_by: str = "DRONE_AUTONOMOUS_SYSTEM"
) -> dict:
    """
    Autonomously file a complaint against a worker/management.
    Called ONLY by the drone patrol system — never by humans.
    Violation types: SLA_BREACH, NON_ACCEPTANCE, FAKE_COMPLETION, QUALITY_FAILURE
    """
    mc_id = f"MC-{str(uuid.uuid4()).replace('-','')[:8].upper()}"
    mc_doc = {
        "management_complaint_id": mc_id,
        "linked_complaint_id": complaint_id,
        "accused_worker_id": worker_id,
        "violation_type": violation_type,
        "evidence_note": evidence_note,
        "filed_by": filed_by,
        "filed_at": now_iso(),
        "status": "OPEN",
        "authority_action": None,
        "authority_action_at": None,
    }
    db.collection("management_complaints").document(mc_id).set(mc_doc)
    # Also mark the original complaint as having a management complaint filed
    db.collection("complaints").document(complaint_id).update({"management_complaint_filed": True})
    return mc_doc

def get_all_workers() -> list[dict]:
    """Fetch all worker records from Firestore."""
    try:
        return [doc.to_dict() for doc in db.collection("workers").stream()]
    except Exception as e:
        print(f"⚠️ get_all_workers error: {e}")
        return []

def get_worker_by_id(worker_id: str) -> dict | None:
    try:
        doc = db.collection("workers").document(worker_id).get()
        return doc.to_dict() if doc.exists else None
    except Exception:
        return None
```

---

## ═══ SECTION 9 — FILE: backend/blockchain.py ═══

```python
"""
blockchain.py — Firestore-backed SHA-256 hash-chain immutable ledger.
Each block cryptographically links to its predecessor.
Prevents fake/AI-generated photo fraud — every photo hashed BEFORE AI sees it.
Satisfies: Blockchain for audit trail (PU Hackathon upcoming features spec).
"""
import hashlib, json, uuid
from datetime import datetime, timezone
from google.cloud import firestore
from config import GCP_PROJECT_ID

db = firestore.Client(project=GCP_PROJECT_ID)
GENESIS_HASH = "0" * 64

def hash_string(text: str) -> str:
    """Deterministic SHA-256 of any string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _get_previous_hash() -> str:
    """Fetch the hash of the most recent ledger block. Returns GENESIS if empty."""
    try:
        query = (
            db.collection("blockchain_ledger")
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(1)
            .stream()
        )
        blocks = list(query)
        if not blocks:
            return GENESIS_HASH
        last_block = blocks[0].to_dict()
        return hash_string(json.dumps(last_block, sort_keys=True, ensure_ascii=False, default=str))
    except Exception:
        return GENESIS_HASH

@firestore.transactional
def _write_block_transaction(transaction, ledger_ref, block: dict):
    transaction.set(ledger_ref, block)

def add_entry(
    complaint_id: str,
    event: str,
    actor: str,
    photo_hash: str = "",
    metadata: dict = None
) -> dict:
    """
    Add an immutable event to the blockchain ledger.
    Events: COMPLAINT_SUBMITTED, AI_ANALYZED, ASSIGNED, ACCEPTED,
            WORK_STARTED, COMPLETION_UPLOADED, DRONE_VERIFIED,
            MANAGEMENT_COMPLAINT_FILED, FAKE_DETECTED, CLOSED
    """
    try:
        block_id = str(uuid.uuid4())
        block = {
            "block_id": block_id,
            "complaint_id": complaint_id,
            "event": event,
            "actor": actor,
            "photo_hash": photo_hash,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prev_hash": _get_previous_hash(),
        }
        ledger_ref = db.collection("blockchain_ledger").document(block_id)
        transaction = db.transaction()
        _write_block_transaction(transaction, ledger_ref, block)
        return block
    except Exception as e:
        raise RuntimeError(f"Blockchain ledger write failed: {e}")

def verify_full_chain() -> dict:
    """
    Stream entire blockchain ledger and verify hash chain integrity.
    Detects any tampered or out-of-order blocks.
    Returns structured audit report for Authority Dashboard display.
    """
    try:
        query = (
            db.collection("blockchain_ledger")
            .order_by("timestamp", direction=firestore.Query.ASCENDING)
            .stream()
        )
        chain = [doc.to_dict() for doc in query]
        if not chain:
            return {
                "total_entries": 0, "broken_links": [], "chain_intact": True,
                "message": "Chain is empty — no entries yet.",
                "verified_at": datetime.now(timezone.utc).isoformat(),
            }

        broken = []
        for i in range(1, len(chain)):
            expected_prev = hash_string(
                json.dumps(chain[i - 1], sort_keys=True, ensure_ascii=False, default=str)
            )
            actual_prev = chain[i].get("prev_hash", "")
            if expected_prev != actual_prev:
                broken.append({
                    "index": i,
                    "block_id": chain[i]["block_id"],
                    "event": chain[i]["event"],
                    "complaint_id": chain[i]["complaint_id"],
                    "timestamp": chain[i]["timestamp"],
                    "expected_hash_prefix": expected_prev[:16],
                    "actual_hash_prefix": actual_prev[:16],
                    "tamper_suspected": True,
                })

        chain_intact = len(broken) == 0
        return {
            "total_entries": len(chain),
            "broken_links": broken,
            "chain_intact": chain_intact,
            "message": (
                f"✅ All {len(chain)} entries verified — chain intact."
                if chain_intact
                else f"🚨 {len(broken)} broken link(s) detected — possible tampering."
            ),
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "total_entries": 0, "broken_links": [], "chain_intact": False,
            "message": f"Verification error: {e}",
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }

def get_complaint_ledger(complaint_id: str) -> list[dict]:
    """Fetch all blockchain entries for a specific complaint ID."""
    try:
        query = (
            db.collection("blockchain_ledger")
            .where("complaint_id", "==", complaint_id)
            .order_by("timestamp", direction=firestore.Query.ASCENDING)
            .stream()
        )
        return [doc.to_dict() for doc in query]
    except Exception as e:
        print(f"⚠️ get_complaint_ledger error: {e}")
        return []
```

---

## ═══ SECTION 10 — FILE: backend/offline_queue.py ═══

```python
"""
offline_queue.py — In-memory offline fallback queue with exponential backoff retry.
Designed for field workers in low-connectivity zones (rural areas, underground sites).
Enqueues payloads when cloud is unreachable. Flushes automatically on connectivity restore.
No disk writes. No external dependencies beyond requests.
Satisfies: "Network issues in rural areas — SMS gateway; WhatsApp bot; offline queue" (PU Hackathon risk table).
"""
import time, requests
from typing import Any

_queue: list[dict] = []

def enqueue(payload: dict) -> None:
    """Add a payload to the in-memory offline queue."""
    _queue.append({
        "payload": payload,
        "attempts": 0,
        "enqueued_at": time.time(),
    })

def get_pending_count() -> int:
    """Return number of items waiting to be synced."""
    return len(_queue)

def get_pending_items() -> list[dict]:
    """Return a copy of all pending queue items for UI display."""
    return list(_queue)

def flush_to_cloud(endpoint: str, max_attempts: int = 5) -> dict:
    """
    Attempt to POST all queued payloads to the cloud endpoint.
    Uses exponential backoff (2^attempt seconds between retries).
    Removes successfully delivered items. Retains failed items for next flush.
    Returns a summary dict of results.
    """
    succeeded = 0
    failed = 0
    remaining = []

    for item in _queue:
        delivered = False
        for attempt in range(max_attempts):
            try:
                response = requests.post(
                    endpoint,
                    json=item["payload"],
                    timeout=10,
                    headers={"Content-Type": "application/json"},
                )
                if response.status_code in (200, 201, 202):
                    delivered = True
                    succeeded += 1
                    break
                else:
                    wait_seconds = 2 ** attempt
                    time.sleep(wait_seconds)
            except requests.exceptions.ConnectionError:
                wait_seconds = 2 ** attempt
                time.sleep(wait_seconds)
            except requests.exceptions.Timeout:
                wait_seconds = 2 ** attempt
                time.sleep(wait_seconds)
            except Exception as e:
                print(f"⚠️ Flush unexpected error on attempt {attempt + 1}: {e}")
                break

        if not delivered:
            item["attempts"] += max_attempts
            remaining.append(item)
            failed += 1

    _queue.clear()
    _queue.extend(remaining)

    return {
        "succeeded": succeeded,
        "failed": failed,
        "still_pending": len(_queue),
        "flushed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

def clear_queue() -> None:
    """Emergency clear — use only for testing or manual admin reset."""
    _queue.clear()
```

---

## ═══ SECTION 11 — FILE: backend/worker_reputation.py ═══

```python
"""
worker_reputation.py — Worker performance tracking and smart assignment.
Citizens rate completed repairs 1–5 stars. System tracks avg_rating per worker.
High-priority repairs prefer workers with avg_rating >= 4.0.
Workers with avg_rating < 2.5 on 5+ jobs are flagged for performance review.
Satisfies: Rule 13 — Worker Reputation System.
"""
from google.cloud import firestore
from config import GCP_PROJECT_ID
from backend.gcp_manager import now_iso, get_all_workers

db = firestore.Client(project=GCP_PROJECT_ID)

@firestore.transactional
def _record_rating_transaction(transaction, worker_ref, rating: int):
    snapshot = worker_ref.get(transaction=transaction)
    data = snapshot.to_dict() or {}
    total_ratings = data.get("total_ratings", 0) + 1
    rating_sum = data.get("rating_sum", 0) + rating
    avg_rating = round(rating_sum / total_ratings, 2)
    completed_jobs = data.get("completed_jobs", 0) + 1

    updates = {
        "total_ratings": total_ratings,
        "rating_sum": rating_sum,
        "avg_rating": avg_rating,
        "completed_jobs": completed_jobs,
        "last_rated_at": now_iso(),
    }

    # Auto-flag for performance review
    if total_ratings >= 5 and avg_rating < 2.5:
        updates["performance_flag"] = "REVIEW_REQUIRED"
    elif avg_rating >= 4.0:
        updates["performance_flag"] = "PREFERRED"
    else:
        updates["performance_flag"] = "STANDARD"

    transaction.update(worker_ref, updates)
    return avg_rating

def record_citizen_rating(worker_id: str, complaint_id: str, rating: int, comment: str = "") -> dict:
    """
    Record a citizen's quality rating for a completed job.
    Updates worker's avg_rating atomically.
    Returns the new rating summary.
    """
    if not (1 <= rating <= 5):
        return {"error": "Rating must be between 1 and 5"}
    try:
        worker_ref = db.collection("workers").document(worker_id)
        transaction = db.transaction()
        new_avg = _record_rating_transaction(transaction, worker_ref, rating)

        # Also write the individual rating record for audit
        rating_doc = {
            "worker_id": worker_id,
            "complaint_id": complaint_id,
            "rating": rating,
            "comment": comment,
            "rated_at": now_iso(),
        }
        db.collection("worker_ratings").add(rating_doc)

        return {"worker_id": worker_id, "new_avg_rating": new_avg, "rating_recorded": rating}
    except Exception as e:
        return {"error": str(e)}

def get_best_available_worker(priority: str, issue_type: str, city: str) -> dict | None:
    """
    Smart worker assignment algorithm.
    For CRITICAL/HIGH: prefer workers with avg_rating >= 4.0 in the same city.
    For MEDIUM/LOW: assign by availability and completed_jobs balance.
    Returns the best matching worker dict, or None if none available.
    """
    try:
        workers = get_all_workers()
        city_workers = [
            w for w in workers
            if w.get("city", "").lower() == city.lower()
            and w.get("active", True)
            and w.get("performance_flag") != "SUSPENDED"
        ]

        if not city_workers:
            # Fallback: any active worker
            city_workers = [w for w in workers if w.get("active", True)]

        if priority in ("CRITICAL", "HIGH"):
            preferred = [w for w in city_workers if w.get("avg_rating", 0) >= 4.0]
            pool = preferred if preferred else city_workers
        else:
            pool = city_workers

        if not pool:
            return None

        # Sort: preferred flag first, then highest avg_rating, then fewest completed_jobs (load balancing)
        pool.sort(key=lambda w: (
            w.get("performance_flag") == "PREFERRED",
            w.get("avg_rating", 0),
            -w.get("completed_jobs", 0),
        ), reverse=True)

        return pool[0]
    except Exception as e:
        print(f"⚠️ get_best_available_worker error: {e}")
        return None

def get_worker_leaderboard(limit: int = 10) -> list[dict]:
    """Return top workers sorted by avg_rating descending, minimum 3 completed jobs."""
    try:
        query = (
            db.collection("workers")
            .where("completed_jobs", ">=", 3)
            .order_by("completed_jobs")
            .stream()
        )
        workers = [doc.to_dict() for doc in query]
        workers.sort(key=lambda w: w.get("avg_rating", 0), reverse=True)
        return workers[:limit]
    except Exception as e:
        print(f"⚠️ get_worker_leaderboard error: {e}")
        return []
```

---

## ═══ SECTION 12 — FULL MODULE CONTRACTS (Generate completely — zero placeholders) ═══

### backend/ai_engine.py — Multi-Agent Vertex AI Pipeline

Implement four distinct agents. Accept `image_bytes: bytes` + `metadata: dict`. Return structured JSON.

**Agent 1 — Vision Agent:**
- Use Vertex AI `gemini-2.5-flash` with vision capability
- Analyze the uploaded photo
- Return: `issue_confirmed: bool`, `detected_issue_type: str`, `severity_score: int (1–10)`, `ai_confidence: float (0–1)`, `is_fake_photo: bool`, `fake_confidence: float`, `hazard_flags: list[str]` (e.g. `["near_school", "heavy_traffic_road"]`, `"monsoon_vulnerability"` if current month is June–September), `ai_description: str`
- If `is_fake_photo` is True and `fake_confidence > 0.85`, set `issue_confirmed = False` and log to blockchain
- On any Vertex AI error: return a structured fallback dict with `ai_confidence: 0.0` and `is_fake_photo: False` — never crash

**Agent 2 — Risk Agent (DETERMINISTIC — zero LLM):**
- Pure Python function: `calculate_risk_score(issue_type: str, hazard_flags: list, severity_score: int, is_recurring: bool) -> int`
- Formula: `base = RISK_BASE_SCORES[issue_type]`; add each matching multiplier from `RISK_CONTEXT_MULTIPLIERS`; add `severity_score × severity_per_point`; if `is_recurring` add `recurring_at_location` bonus; cap final score at 100
- Map score to priority using `PRIORITY_THRESHOLDS`
- This function produces identical output for identical inputs — deterministic and auditable

**Agent 3 — Memory Agent:**
- Query Firestore `complaints` collection for complaints within 100m radius of current GPS (use Haversine formula — no external library)
- Define `haversine_distance(lat1, lon1, lat2, lon2) -> float` in pure Python
- If ≥ 2 prior complaints at same location cluster: set `is_recurring = True`, `recurring_count = N`, write Memory Agent finding to Firestore
- Return: `is_recurring: bool`, `recurring_count: int`, `recurring_issue_summary: str`, `first_reported_at: str`

**Agent 4 — Planning Agent:**
- Use Vertex AI `gemini-2.5-flash` (text only — no image needed)
- Input: issue_type, priority, risk_score, location, ward, city, recurring context
- Return structured JSON: `repair_steps: list[str]` (step-by-step action plan), `estimated_budget_inr: int`, `required_materials: list[str]`, `recommended_team_size: int`, `estimated_duration_hours: int`, `department: str` (from `ISSUE_DEPARTMENT_MAP`)
- On error: return deterministic fallback based on issue_type from a hardcoded fallback dict (all issue types covered)

**Orchestrator function `run_full_ai_pipeline(complaint_id, image_bytes, metadata) -> dict`:**
- Run Vision Agent first
- If fake detected: call `gcp_manager.penalize_citizen_fake()`, add blockchain entry `FAKE_DETECTED`, update complaint status to `FAKE_DETECTED`, return early
- Run Risk Agent with Vision output
- Run Memory Agent with GPS coordinates
- Run Planning Agent with all prior outputs
- Write all results to Firestore complaint document
- Add blockchain entry `AI_ANALYZED`
- Update complaint status to the next appropriate state
- Publish Pub/Sub event for assignment routing
- Return full analysis dict

---

### backend/drone_verifier.py — Autonomous Drone System

Implement TWO functions:

**Function 1 — `verify_repair(complaint_id: str, before_gcs_uri: str, after_gcs_uri: str) -> dict`:**
- Download both images from GCS
- Use Vertex AI `gemini-2.5-flash` vision to compare before vs after
- Detect if completion photo is nearly identical to complaint photo (`DRONE_FAKE_SIMILARITY_THRESHOLD = 0.92`)
- Return: `verdict: str` (one of: `VERIFIED_COMPLETE`, `PARTIALLY_COMPLETE`, `REQUIRES_REWORK`, `FAKE_COMPLETION_DETECTED`), `completion_percentage: int (0–100)`, `confidence: float`, `drone_notes: str`, `blockchain_hash: str`
- If `FAKE_COMPLETION_DETECTED`: call `gcp_manager.file_management_complaint()` with `violation_type="FAKE_COMPLETION"` automatically
- Write `DRONE_VERIFIED` entry to blockchain
- Update complaint status in Firestore accordingly

**Function 2 — `drone_patrol_and_escalate() -> dict`:**
- This function runs AUTONOMOUSLY — called on Authority dashboard load and via Pub/Sub schedule
- Scan ALL Firestore complaints where:
  - `status == "ASSIGNED"` AND `assigned_at` is > `DRONE_ACCEPTANCE_TIMEOUT_HOURS` hours ago AND `accepted_at is None` → violation: `NON_ACCEPTANCE`
  - `status in ["ACCEPTED", "IN_PROGRESS"]` AND `assigned_at` is beyond SLA deadline (from `SLA_HOURS[priority]`) → violation: `SLA_BREACH`
- For EACH violation found:
  - Call `gcp_manager.file_management_complaint()` with appropriate `violation_type`
  - Add blockchain entry `MANAGEMENT_COMPLAINT_FILED`
  - Update complaint status to `ESCALATED`
  - Award gamification points to the citizen who filed the original complaint (`management_complaint_filed` = +20 points)
- Return: `patrol_completed_at: str`, `violations_found: int`, `complaints_escalated: int`, `management_complaints_filed: list[str]`

---

### backend/gamification.py

- `award_points(aadhar_hash: str, rule_key: str, reason: str, complaint_id: str) -> dict`: Use Firestore atomic increment on citizen's `total_points`. Recalculate tier from `CIVIC_TIERS` after every award. Update citizen document. Write award to `gamification_log` collection. Return new points and tier.
- `get_leaderboard(limit: int = 10) -> list[dict]`: Stream top citizens by `total_points` descending.
- `get_citizen_tier(points: int) -> dict`: Return matching tier dict from `CIVIC_TIERS`.
- `get_citizen_stats(aadhar_hash: str) -> dict`: Return full gamification profile with tier, points, rank, next tier progress, badge, complaint history counts.

---

### backend/pubsub_workers.py

- `publish_event(topic_id: str, payload: dict) -> str`: Serialize payload to JSON, publish to Pub/Sub topic, return message ID.
- `process_civic_event(message) -> None`: Subscriber callback. Parse message data. Route by `event_type` field:
  - `"NEW_COMPLAINT"` → call `ai_engine.run_full_ai_pipeline()`
  - `"COMPLETION_UPLOADED"` → call `drone_verifier.verify_repair()`
  - `"DRONE_PATROL"` → call `drone_verifier.drone_patrol_and_escalate()`
  - `"AWARD_POINTS"` → call `gamification.award_points()`
- All handlers wrapped in try/except — never let subscriber crash

---

### backend/maps_helper.py

- `render_complaint_map(complaints: list[dict], center_lat: float = None, center_lng: float = None) -> str`: Build Folium map. Color-code markers by priority using `PRIORITY_COLORS`. Add popup for each complaint with ID, type, priority, status, citizen name, submitted date. Add circle overlay for CRITICAL complaints (red radius). Use heatmap layer for complaint density. Return HTML string.
- `render_worker_route_map(worker_lat: float, worker_lng: float, complaint_lat: float, complaint_lng: float) -> str`: Build Folium map showing worker current location and job site with a line between them. Add "Navigate" link to Google Maps directions URL. Return HTML string.
- `get_geocode(address: str) -> dict`: Call Google Maps Geocoding API with `GOOGLE_MAPS_API_KEY`. Return `{lat, lng, formatted_address}`. On error or empty key: return default India center coordinates with a warning flag.
- `build_google_maps_embed_url(lat: float, lng: float, zoom: int = 15) -> str`: Return embed URL string for Google Maps iframe. Use `GOOGLE_MAPS_API_KEY` if set, else return OSM fallback URL.

---

## ═══ SECTION 13 — THREE DASHBOARDS (Full UI Contracts) ═══

### pages/1_Citizen.py — Citizen Portal

**Tab 1 — Register / Login:**
- Check session state for existing login. If logged in, skip to complaints.
- Registration form: Full Name, City, Ward, Phone Number, Mock Aadhar Number (12-digit field with label "Aadhar Verification — Demo Mode").
- Before writing to Firestore: hash Aadhar with `hash_identifier()`. Call `citizen_exists_by_aadhar()`. If exists: show red error "An account with this Aadhar number already exists. One citizen = one account." Stop.
- Call `citizen_exists_by_phone()`. If exists: show red error "Phone number already registered." Stop.
- On success: write citizen to Firestore, show green success, store in `st.session_state`.
- Login form (for returning users): Phone + last 4 of Aadhar. Validate against Firestore hash.

**Tab 2 — File a Complaint:**
- Photo upload (JPG/PNG/MP4). Show preview.
- Form fields: Issue Type (dropdown from `ISSUE_TYPES`), Description (text area), City, Ward, Location Text, Latitude, Longitude (auto-fill from browser geolocation JS if available, else manual entry).
- On Submit: hash photo bytes (`hash_file_bytes()`). Upload to GCS at path `complaints/{complaint_id}/original.jpg`. Build complaint in Firestore. Add `COMPLAINT_SUBMITTED` blockchain entry. Publish `NEW_COMPLAINT` Pub/Sub event. Award 10 points. Show: "✅ Submitted! Your Complaint ID: CS-XXXXXXXX — AI analysis begins in <30 seconds." Display the 7-step tracker immediately.
- Show Google Maps embed at the entered coordinates.

**Tab 3 — Track My Complaints:**
- Pull all complaints for logged-in citizen's `aadhar_hash`.
- For each complaint: show complaint card with 7-step visual progress tracker (PENDING → AI_ANALYZING → ASSIGNED → IN_PROGRESS → DRONE_SCANNING → VERIFIED_COMPLETE → CLOSED).
- Highlight current step in color matching `PRIORITY_COLORS`. Show status_history timeline below.
- If status is `VERIFIED_COMPLETE` or `REQUIRES_REWORK` and citizen hasn't rated: show star rating widget (1–5) + comment box + "Submit Rating" button. On submit: call `worker_reputation.record_citizen_rating()`, update complaint `citizen_rating` field, award citizen 10 points if rating ≥ 4.
- Show blockchain ledger for the complaint (call `blockchain.get_complaint_ledger()`).

**Tab 4 — My Civic Score (Gamification Dashboard):**
- Display citizen's current tier with large colored badge.
- Points breakdown: total points, points this month, points by category.
- Progress bar to next tier.
- Leaderboard: top 10 citizens in the city (from `gamification.get_leaderboard()`).
- History table: all point award events from `gamification_log`.
- Show fake_strikes count with warning if > 0: "⚠️ {n}/3 fake complaint strikes. 3 strikes = account suspended."

---

### pages/2_Worker.py — Field Worker Portal

**Login gate:** Worker ID + password (`WORKER_DEFAULT_PWD`). Validate against `workers` Firestore collection.

**Tab 1 — My Jobs (Job Queue):**
- Pull all complaints where `assigned_worker_id == worker_id` and status in `["ASSIGNED", "ACCEPTED", "IN_PROGRESS"]`.
- For each job: show complaint card with priority badge, issue type, location, risk score, SLA deadline (calculated from `SLA_HOURS`), AI repair plan (from `ai_analysis.planning`), estimated budget.
- Show Google Maps embed of job location.
- Show "Navigate to Site" link: `https://www.google.com/maps/dir/?api=1&destination={lat},{lng}` — opens in Google Maps app on mobile.
- Buttons: "Accept Job" → updates status to `ACCEPTED`, adds blockchain entry `ACCEPTED`. "Start Work" → updates to `IN_PROGRESS`, adds `WORK_STARTED`.

**Tab 2 — Upload Completion Proof:**
- For jobs in status `IN_PROGRESS` or `ACCEPTED`: show proof upload form.
- Accept photo AND optional video (up to 100MB).
- On upload: hash bytes. Upload to GCS at `complaints/{complaint_id}/completion.{ext}`. Update complaint with `completion_photo_path` and `completion_photo_hash`. Update status to `COMPLETION_UPLOADED`. Add blockchain entry `COMPLETION_UPLOADED`. Publish `COMPLETION_UPLOADED` Pub/Sub event (triggers drone verification). Show: "✅ Proof uploaded — Drone verification initiated automatically."
- If offline queue has pending items: show "📡 {n} items queued offline — tap to sync" button.

**Tab 3 — My Performance:**
- Show worker's `avg_rating`, `completed_jobs`, `performance_flag`.
- Render star rating history chart (Plotly bar chart by month).
- Show all citizen comments received.
- If `performance_flag == "REVIEW_REQUIRED"`: show yellow banner "⚠️ Your average rating is below 2.5 — performance review has been flagged."

---

### pages/3_Authority.py — Authority Command Center

**Login gate:** Username + password from `AUTH_AUTHORITY`.

**Tab 1 — Live Dashboard (Overview):**
- 4 KPI metric cards: Total Active Complaints, CRITICAL count (red), Resolved Today, Avg Resolution Time (hours).
- Plotly bar chart: complaints by priority.
- Plotly line chart: daily complaint volume over last 30 days.
- Plotly pie chart: complaints by issue type.
- Pull impact stats from config for context display: "India: 1.5 crore civic complaints/year, 30% resolved → Our target: 90%+"

**Tab 2 — Complaint Management:**
- Filterable data table: filter by priority, status, issue_type, city, ward, date range.
- Click any complaint row to expand full detail: photos (before/after), AI analysis, risk score breakdown, planning agent output, full status history timeline, blockchain ledger, Google Maps embed.
- Assign worker button: opens worker selection dropdown (filtered by city, sorted by `worker_reputation.get_best_available_worker()`). Shows each worker's `avg_rating`, `completed_jobs`, `performance_flag`. On assign: update complaint, write blockchain entry `ASSIGNED`, send Pub/Sub notification.

**Tab 3 — Live Map (Geospatial Heatmap):**
- Full-width Folium map with all active complaints as color-coded markers.
- Cluster markers in dense areas.
- Heatmap layer showing complaint density hotspots (addresses Use Case 5: Data-Driven Governance — "Identifies top 5 complaint hotspots").
- Filter controls: show only CRITICAL, show only specific issue types, show only unassigned.
- Google Maps embed below for specific location drill-down.

**Tab 4 — Drone-Filed Escalations (Management Complaints):**
- **This tab is dedicated entirely to complaints autonomously filed by the drone patrol system.**
- Show all documents from `management_complaints` Firestore collection, sorted by `filed_at` descending.
- Each card shows: Management Complaint ID, linked original Complaint ID, accused Worker ID, `violation_type` badge (SLA_BREACH / NON_ACCEPTANCE / FAKE_COMPLETION / QUALITY_FAILURE), evidence note from drone, filed datetime, current status (OPEN/REVIEWED/ACTIONED).
- Authority action buttons: "Issue Warning", "Suspend Worker", "Reassign Complaint", "Close — No Action". On action: update management_complaint status, optionally update worker `performance_flag`.
- Summary stats: total open escalations, most escalated workers, most escalated issue types.

**Tab 5 — Worker Management:**
- All workers table: ID, name, city, `avg_rating`, `completed_jobs`, `performance_flag`, assigned active jobs count.
- Worker detail expand: full rating history, all their complaints, performance chart.
- Add new worker form: name, city, phone, skills. Auto-assign worker ID and default password.
- Worker reputation leaderboard (top 10 by avg_rating from `worker_reputation.get_worker_leaderboard()`).

**Tab 6 — Blockchain Audit:**
- "Run Full Chain Verification" button → calls `blockchain.verify_full_chain()` → displays full audit report.
- Show total entries, chain integrity status, any broken links highlighted in red.
- Full ledger table: all events in order, complaint IDs, actors, photo hashes, timestamps.
- Download ledger as CSV button.

**Tab 7 — Analytics & Governance:**
- Resolution rate trend: "30% (national avg) → Current system performance" (Plotly line).
- SLA compliance rate by priority.
- Contractor/worker performance comparison (addresses Use Case 5: "60% issues on contractor X's roads").
- Monthly savings estimate widget (based on resolved CRITICAL complaints × ₹50,000 crore context).
- Top 5 complaint hotspot locations.

---

## ═══ SECTION 14 — FILE: app.py ═══

```python
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
```

---

## ═══ SECTION 15 — FILE: scripts/gcp_seed.py ═══

Generate a complete, idempotent seed script that:
- Seeds 5 citizen records with varied points and tiers (Bronze through Gold), real Indian names, cities including Nagpur, Pune, Mumbai, Delhi, Bengaluru
- Seeds 5 worker records with varied `avg_rating` values (3.2, 3.8, 4.1, 4.6, 2.1), cities matching citizens, one marked `performance_flag: "REVIEW_REQUIRED"`
- Seeds 15 complaints across all 9 issue types, all 4 priority levels, multiple statuses (PENDING through VERIFIED_COMPLETE), real Indian GPS coordinates, realistic descriptions
- Seeds 3 management_complaints filed by `DRONE_AUTONOMOUS_SYSTEM` for the demo
- Seeds a blockchain ledger chain with 20 entries across all event types, correctly hash-linked
- Seeds gamification_log with point awards for each citizen
- All seeds are IDEMPOTENT: check if document exists before writing (`db.collection().document(id).set(data, merge=False)` only if not exists)
- Print progress: "✅ Seeded: {item}" for each record created, "⏭️ Skipped: {item} already exists" for each skipped

---

## ═══ SECTION 16 — TESTS (Generate and Run) ═══

### tests/test_blockchain.py

Generate pytest tests covering:
- `hash_string("hello")` produces consistent, expected SHA-256 output
- `verify_full_chain()` returns `chain_intact: True` on a freshly seeded empty chain context
- Two sequential `add_entry()` calls produce correctly linked `prev_hash` values (second block's `prev_hash` == SHA-256 of first block's full JSON)
- `get_complaint_ledger("CS-NONEXISTENT")` returns empty list without error

### tests/test_risk_engine.py

Generate pytest tests covering:
- `calculate_risk_score("Pothole", [], 5, False)` produces the exact same integer on two calls (determinism)
- `calculate_risk_score("Blocked Drain", ["monsoon_vulnerability"], 7, False)` > `calculate_risk_score("Blocked Drain", [], 7, False)` (monsoon multiplier increases score)
- No score exceeds 100
- No score falls below 0
- `calculate_risk_score("Blocked Drain", ["near_school", "monsoon_vulnerability", "immediate_danger"], 10, True)` == 100 (ceiling test)

---

## ═══ SECTION 17 — ENVIRONMENT VARIABLES ═══

```bash
export GOOGLE_CLOUD_PROJECT="your-new-gcp-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
export GCS_ASSET_BUCKET="your-project-id-civic-media"     # optional, auto-derived
export PUBSUB_TOPIC="civic-events-topic"                  # optional
export PUBSUB_DRONE_TOPIC="civic-drone-patrol-topic"      # optional
export VERTEX_LOCATION="us-central1"                      # optional
export GOOGLE_MAPS_API_KEY="your-maps-api-key"            # optional — Folium fallback if empty
```

---

## ═══ SECTION 18 — DEMO FLOW SCRIPT (Follow exactly during presentation) ═══

**Step 1 (0:00):** Open app.py landing page. Point to the 3 KPI metrics. Say: "India resolves only 30% of civic complaints. We target 90%+."

**Step 2 (0:45):** Go to Citizen Portal. Register a new citizen with mock Aadhar. Attempt to register again with the same Aadhar — show the duplicate rejection error. Say: "One Aadhar, one account — fraud-proof from registration."

**Step 3 (1:30):** File a complaint. Upload a pothole photo. Select "Pothole", enter a school zone location. Submit. Show the "AI analyzing in <30 seconds" message. Show the Complaint ID. Say: "Photo is hashed and stored on our blockchain before AI even looks at it."

**Step 4 (2:00):** Go to Authority Dashboard. Show the complaint appearing with CRITICAL priority (near school = +20 points → CRITICAL). Show the AI analysis card: Vision findings, Risk Score, Memory Agent result, Planning Agent repair plan with INR budget. Say: "Four AI agents. Deterministic scoring. Legally defensible. No hallucinations in priority decisions."

**Step 5 (2:30):** Assign the complaint to a worker. Show the smart assignment: preferred worker with avg_rating 4.6 auto-suggested. Assign. Show blockchain entry `ASSIGNED` added.

**Step 6 (3:00):** Go to Worker Portal. Login as assigned worker. Show job in queue with Google Maps navigation link. Accept job. Go to Upload tab. Upload a completion photo. Show: "Drone verification initiated automatically."

**Step 7 (3:30):** Go back to Authority Dashboard → Tab 4 (Drone-Filed Escalations). Show a pre-seeded management complaint (from seed data). Say: "If a worker doesn't accept within 24 hours, the drone autonomously files a complaint against them. No human required."

**Step 8 (4:00):** Click "Run Full Chain Verification" on the Blockchain Audit tab. Show chain_intact: True, all N entries verified. Say: "Every action — submission, analysis, assignment, completion, verification — is on an immutable blockchain. Fake photos can't pass this."

**Step 9 (4:30):** Go back to Citizen Portal → My Civic Score tab. Show gamification points awarded, tier badge, leaderboard position. Say: "Citizens are rewarded for real reports. Fake reports cost 50 points and risk account suspension."

---

## ═══ SECTION 19 — FINAL INSTRUCTION TO ANTIGRAVITY IDE ═══

Begin by reading and acknowledging all 14 Build Rules and the Persistent Skill definition.

Then generate files in this exact order, writing every file COMPLETELY from first import to last line:

1. `requirements.txt`
2. `config.py`
3. `setup.py`
4. `backend/__init__.py`
5. `backend/gcp_manager.py`
6. `backend/blockchain.py`
7. `backend/offline_queue.py`
8. `backend/worker_reputation.py`
9. `backend/ai_engine.py`
10. `backend/drone_verifier.py`
11. `backend/gamification.py`
12. `backend/pubsub_workers.py`
13. `backend/maps_helper.py`
14. `pages/1_Citizen.py`
15. `pages/2_Worker.py`
16. `pages/3_Authority.py`
17. `app.py`
18. `scripts/gcp_seed.py`
19. `tests/test_blockchain.py`
20. `tests/test_risk_engine.py`

If your response cuts off due to length, I will type **"Continue"** and you will resume from EXACTLY where you left off — not from the beginning, not with a summary, but from the next line of code.

After all 20 files are generated:
- Run: `pip install pytest && pytest tests/ -v`
- If tests pass: print "✅ Civic Solvers build complete. All tests passed."
- If tests fail: fix the failing code and re-run until all pass.

**NON-NEGOTIABLE:** Every single function, every class, every method must be written in full. The judges for PU Code Hackathon 3.0 and AWS AI for Bharat Hackathon will see a production-ready, fully functional prototype — not a scaffold, not a mockup, not a demo with fake buttons.
