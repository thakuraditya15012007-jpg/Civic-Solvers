# backend/offline_queue.py
"""
Thread-safe in-memory offline queue for complaint processing.
Used when Pub/Sub is unavailable (local / mock mode).

ALL functions that any other file might call are defined here.
No AttributeError will ever be raised from this module.
"""
import threading
import datetime
import uuid
from typing import Any

_queue: list  = []
_lock         = threading.Lock()
_processed: list = []


def enqueue(item: dict) -> str:
    """Add an item to the offline queue. Returns a queue item ID."""
    with _lock:
        item_id = str(uuid.uuid4())
        _queue.append({
            "id":         item_id,
            "data":       item,
            "enqueued_at":datetime.datetime.utcnow().isoformat(),
            "status":     "pending",
        })
        return item_id


def dequeue() -> dict | None:
    """Pop the next pending item. Returns None if queue is empty."""
    with _lock:
        for entry in _queue:
            if entry["status"] == "pending":
                entry["status"] = "processing"
                return entry
        return None


def mark_done(item_id: str):
    """Mark an item as successfully processed."""
    with _lock:
        for entry in _queue:
            if entry["id"] == item_id:
                entry["status"]       = "done"
                entry["processed_at"] = datetime.datetime.utcnow().isoformat()
                _processed.append(entry)
                break


def mark_failed(item_id: str, error: str = ""):
    """Mark an item as failed so it can be retried."""
    with _lock:
        for entry in _queue:
            if entry["id"] == item_id:
                entry["status"] = "failed"
                entry["error"]  = error
                break


def get_queue_size() -> int:
    """
    FIX-01: This function was missing — causing AttributeError in Worker page.
    Returns total number of items in the queue (all statuses).
    """
    with _lock:
        return len(_queue)


def get_pending_count() -> int:
    """Returns count of items still waiting to be processed."""
    with _lock:
        return sum(1 for e in _queue if e["status"] == "pending")


def get_processing_count() -> int:
    """Returns count of items currently being processed."""
    with _lock:
        return sum(1 for e in _queue if e["status"] == "processing")


def get_failed_count() -> int:
    """Returns count of failed items."""
    with _lock:
        return sum(1 for e in _queue if e["status"] == "failed")


def get_all_items() -> list:
    """Returns a snapshot of all queue items (for Authority dashboard display)."""
    with _lock:
        return list(_queue)


def get_queue_stats() -> dict:
    """Returns a full stats dict — safe to call from any page."""
    with _lock:
        total      = len(_queue)
        pending    = sum(1 for e in _queue if e["status"] == "pending")
        processing = sum(1 for e in _queue if e["status"] == "processing")
        done       = sum(1 for e in _queue if e["status"] == "done")
        failed     = sum(1 for e in _queue if e["status"] == "failed")
    return {
        "total":      total,
        "pending":    pending,
        "processing": processing,
        "done":       done,
        "failed":     failed,
    }


def clear_done():
    """Remove all completed items from the queue."""
    with _lock:
        global _queue
        _queue = [e for e in _queue if e["status"] != "done"]


def reset():
    """Full reset — used in tests only."""
    with _lock:
        global _queue, _processed
        _queue     = []
        _processed = []
