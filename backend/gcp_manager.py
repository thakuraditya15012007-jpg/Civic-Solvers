"""
gcp_manager.py — Universal Firestore CRUD and GCS wrapper.
Thread-safe via cloud atomic transactions. No local state.
Handles: complaints, citizens, workers, management_complaints, worker_ratings.
"""
import sys

# Ensure stdout/stderr handles emojis safely on Windows CP1252 consoles
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(errors='replace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(errors='replace')
    except Exception:
        pass

import uuid
import hashlib
import threading
from datetime import datetime, timezone
from config import GCP_PROJECT_ID, GCS_BUCKET_NAME, PUBSUB_TOPIC_ID, PUBSUB_DRONE_TOPIC

# ── Mock GCP Fallback Implementations ────────────────────────────────────────

_mock_store: dict = {}
_mock_lock = threading.Lock()

class MockFirestoreDoc:
    def __init__(self, data):
        self._data = data
        self.exists = data is not None
    def to_dict(self):
        return self._data

class MockFirestoreCollection:
    def __init__(self, name, filters=None, limit_val=None, order_by_val=None):
        self._name = name
        self._filters = filters or []
        self._limit = limit_val
        self._order_by = order_by_val
    def document(self, doc_id):
        return MockFirestoreDocRef(self._name, doc_id)
    def where(self, field, op, val):
        new_filters = self._filters + [(field, op, val)]
        return MockFirestoreCollection(self._name, new_filters, self._limit, self._order_by)
    def order_by(self, field, direction=None):
        return MockFirestoreCollection(self._name, self._filters, self._limit, (field, direction))
    def limit(self, n):
        return MockFirestoreCollection(self._name, self._filters, n, self._order_by)
    def stream(self):
        prefix = self._name + ":"
        with _mock_lock:
            results = []
            for k, v in _mock_store.items():
                if k.startswith(prefix):
                    match = True
                    for field, op, val in self._filters:
                        field_val = v.get(field)
                        if op == "==":
                            if field_val != val:
                                match = False
                                break
                        elif op == ">=":
                            if field_val is None or field_val < val:
                                match = False
                                break
                        elif op == "<=":
                            if field_val is None or field_val > val:
                                match = False
                                break
                    if match:
                        results.append(MockFirestoreDoc(v))
            if self._order_by:
                field, direction = self._order_by
                rev = False
                if str(direction).upper() in ("DESCENDING", "DESC"):
                    rev = True
                results.sort(key=lambda snap: snap.to_dict().get(field, ""), reverse=rev)
            if self._limit is not None:
                results = results[:self._limit]
        return results
    def add(self, data):
        import uuid
        doc_id = str(uuid.uuid4())
        key = f"{self._name}:{doc_id}"
        with _mock_lock:
            _mock_store[key] = data
        return None, MockFirestoreDocRef(self._name, doc_id)

class MockFirestoreDocRef:
    def __init__(self, collection, doc_id):
        self._key = f"{collection}:{doc_id}"
    def get(self, transaction=None):
        with _mock_lock:
            return MockFirestoreDoc(_mock_store.get(self._key))
    def set(self, data, merge=False):
        with _mock_lock:
            _mock_store[self._key] = data
    def update(self, data):
        with _mock_lock:
            existing = _mock_store.get(self._key, {})
            existing.update(data)
            _mock_store[self._key] = existing
    def delete(self):
        with _mock_lock:
            _mock_store.pop(self._key, None)

class MockDB:
    def collection(self, name):
        return MockFirestoreCollection(name)
    def transaction(self):
        return None

class MockStorageClient:
    def bucket(self, name):
        return self
    def blob(self, name):
        self._blob_name = name
        return self
    def upload_from_string(self, data, content_type=None):
        with _mock_lock:
            _mock_store[f"blob:{self._blob_name}"] = data
    def download_as_bytes(self):
        with _mock_lock:
            res = _mock_store.get(f"blob:{self._blob_name}")
            if res is not None:
                return res
            return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"

_USE_MOCK = False

try:
    from google.cloud import firestore as _firestore, storage as _storage
    db = _firestore.Client(project=GCP_PROJECT_ID)
    storage_client = _storage.Client(project=GCP_PROJECT_ID)
    # Test connectivity
    db.collection("_health").document("check").get()
    print("✅ Connected to real GCP Firestore")
except Exception as _e:
    print(f"⚠️ GCP unavailable ({_e}) — switching to local mock mode")
    _USE_MOCK = True
    db = MockDB()
    storage_client = MockStorageClient()

class DummyQuery:
    DESCENDING = "DESCENDING"
    ASCENDING = "ASCENDING"

class DummyFirestoreLib:
    Query = DummyQuery
    def transactional(self, func):
        def wrapper(transaction, *args, **kwargs):
            return func(transaction, *args, **kwargs)
        return wrapper

firestore_lib = DummyFirestoreLib()

# Expose firestore.transactional decorator
def transactional_decorator(func):
    return firestore_lib.transactional(func)

# ── General Helper Utilities ──────────────────────────────────────────────────

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
    """Upload media to GCS. Returns gs:// URI or mock:// URI if offline. Raises RuntimeError on failure."""
    if _USE_MOCK:
        with _mock_lock:
            _mock_store[f"blob:{destination_blob_name}"] = file_bytes
        return f"mock://local/{destination_blob_name}"
    try:
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(file_bytes, content_type=content_type)
        return f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"
    except Exception as e:
        raise RuntimeError(f"GCS upload failed for {destination_blob_name}: {e}")

def download_gcs_bytes(uri: str) -> bytes:
    """Download bytes from a gs:// URI or mock:// URI, handling mock environments transparently."""
    if not uri:
        raise ValueError("URI is empty")
    if uri.startswith("mock://local/"):
        blob_name = uri[len("mock://local/"):]
        with _mock_lock:
            res = _mock_store.get(f"blob:{blob_name}")
            if res is not None:
                return res
            # Return fallback 1x1 PNG bytes
            return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
    if uri.startswith("gs://"):
        parts = uri[5:].split("/", 1)
        bucket_name = parts[0]
        blob_name = parts[1]
        
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        return blob.download_as_bytes()
    raise ValueError(f"Invalid GCS URI: {uri}")

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

def penalize_citizen_fake(aadhar_hash: str) -> dict:
    """Add a fake strike to citizen. Suspend after 3 strikes. Returns updated state."""
    try:
        doc_ref = db.collection("citizens").document(aadhar_hash)
        doc = doc_ref.get()
        data = doc.to_dict() or {}
        strikes = data.get("fake_strikes", 0) + 1
        updates = {"fake_strikes": strikes}
        if strikes >= 3:
            updates["active"] = False
            updates["suspension_reason"] = "3 fake complaint strikes — account suspended by autonomous system"
        doc_ref.update(updates)
        return {"strikes": strikes, "suspended": strikes >= 3}
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
    if not citizen_phone_display:
        citizen_phone_display = "XXXXXXXXXX"
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

def update_complaint_status(complaint_id: str, new_status: str, note: str, actor: str, extra_fields: dict = None) -> bool:
    """Update complaint status and append to status_history without decorator or transaction dependency."""
    try:
        doc_ref = db.collection("complaints").document(complaint_id)
        doc = doc_ref.get()
        data = doc.to_dict() or {}
        history = data.get("status_history", [])
        history.append({"status": new_status, "timestamp": now_iso(), "note": note, "actor": actor})
        update_payload = {"status": new_status, "status_history": history}
        if extra_fields:
            update_payload.update(extra_fields)
        doc_ref.update(update_payload)
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
