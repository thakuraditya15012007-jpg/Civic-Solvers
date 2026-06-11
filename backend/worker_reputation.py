"""
worker_reputation.py — Worker performance tracking and smart assignment.
Citizens rate completed repairs 1–5 stars. System tracks avg_rating per worker.
High-priority repairs prefer workers with avg_rating >= 4.0.
Workers with avg_rating < 2.5 on 5+ jobs are flagged for performance review.
Satisfies: Rule 13 — Worker Reputation System.
"""
from backend.gcp_manager import db, now_iso, get_all_workers, firestore_lib

def record_citizen_rating(worker_id: str, complaint_id: str, rating: int, comment: str = "") -> dict:
    """
    Record a citizen's quality rating for a completed job.
    Updates worker's avg_rating directly.
    Returns the new rating summary.
    """
    if not (1 <= rating <= 5):
        return {"error": "Rating must be between 1 and 5"}
    try:
        worker_ref = db.collection("workers").document(worker_id)
        doc = worker_ref.get()
        data = doc.to_dict() or {}
        
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

        worker_ref.update(updates)

        # Also write the individual rating record for audit
        rating_doc = {
            "worker_id": worker_id,
            "complaint_id": complaint_id,
            "rating": rating,
            "comment": comment,
            "rated_at": now_iso(),
        }
        db.collection("worker_ratings").add(rating_doc)

        return {"worker_id": worker_id, "new_avg_rating": avg_rating, "rating_recorded": rating}
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
        # Stream and sort in Python to be fully compatible with local mock database
        workers = get_all_workers()
        valid_workers = [w for w in workers if w.get("completed_jobs", 0) >= 3]
        valid_workers.sort(key=lambda w: w.get("avg_rating", 0), reverse=True)
        return valid_workers[:limit]
    except Exception as e:
        print(f"⚠️ get_worker_leaderboard error: {e}")
        return []
