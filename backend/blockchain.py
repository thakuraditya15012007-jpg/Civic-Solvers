"""
blockchain.py — Firestore-backed SHA-256 hash-chain immutable ledger.
Each block cryptographically links to its predecessor.
Prevents fake/AI-generated photo fraud — every photo hashed BEFORE AI sees it.
Satisfies: Blockchain for audit trail (PU Hackathon upcoming features spec).
"""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from backend.gcp_manager import db, firestore_lib

GENESIS_HASH = "0" * 64

def hash_string(text: str) -> str:
    """Deterministic SHA-256 of any string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _get_previous_hash() -> str:
    """Fetch the hash of the most recent ledger block. Returns GENESIS if empty."""
    try:
        # Determine the order direction from firestore_lib
        order_dir = getattr(firestore_lib.Query, "DESCENDING", "DESCENDING")
        query = (
            db.collection("blockchain_ledger")
            .order_by("timestamp", direction=order_dir)
            .limit(1)
            .stream()
        )
        blocks = list(query)
        if not blocks:
            return GENESIS_HASH
        last_block = blocks[0].to_dict()
        return hash_string(json.dumps(last_block, sort_keys=True, ensure_ascii=False, default=str))
    except Exception as e:
        print(f"⚠️ _get_previous_hash warning: {e}")
        return GENESIS_HASH

def add_entry(complaint_id, event, actor, photo_hash="", metadata=None):
    try:
        import uuid
        from datetime import datetime, timezone
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
        db.collection("blockchain_ledger").document(block_id).set(block)
        return block
    except Exception as e:
        print(f"Blockchain write error: {e}")
        return {"block_id": "error", "event": event, "error": str(e)}

def verify_full_chain() -> dict:
    """
    Stream entire blockchain ledger and verify hash chain integrity.
    Detects any tampered or out-of-order blocks.
    Returns structured audit report for Authority Dashboard display.
    """
    try:
        order_dir = getattr(firestore_lib.Query, "ASCENDING", "ASCENDING")
        query = (
            db.collection("blockchain_ledger")
            .order_by("timestamp", direction=order_dir)
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
        order_dir = getattr(firestore_lib.Query, "ASCENDING", "ASCENDING")
        query = (
            db.collection("blockchain_ledger")
            .where("complaint_id", "==", complaint_id)
            .order_by("timestamp", direction=order_dir)
            .stream()
        )
        return [doc.to_dict() for doc in query]
    except Exception as e:
        print(f"⚠️ get_complaint_ledger error: {e}")
        return []
