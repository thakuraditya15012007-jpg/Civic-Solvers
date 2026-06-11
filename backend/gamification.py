"""
gamification.py — Civic Points and Reputation Management.
Atomic updates to citizen scores, tier leveling, badges, and city-wide leaderboards.
Satisfies: Gamification Tiers (Bronze to Diamond) and Point Rules.
"""
from config import CIVIC_TIERS, POINT_RULES
from backend.gcp_manager import db, now_iso, firestore_lib

def get_citizen_tier(points: int) -> dict:
    """Return matching tier dict from CIVIC_TIERS based on points."""
    for tier in CIVIC_TIERS:
        if tier["min"] <= points <= tier["max"]:
            return tier
    return CIVIC_TIERS[0]

def award_points(aadhar_hash: str, rule_key: str, reason: str, complaint_id: str) -> dict:
    """
    Awards (or penalizes) points to a citizen document directly without transaction decorators.
    Saves the audit transaction in gamification_log.
    """
    points_to_add = POINT_RULES.get(rule_key, 0)
    if points_to_add == 0 and rule_key != "fake_strike_recorded":
        return {"error": f"Invalid rule key or zero points award: {rule_key}"}

    try:
        citizen_ref = db.collection("citizens").document(aadhar_hash)
        doc = citizen_ref.get()
        data = doc.to_dict() or {}
        
        old_points = data.get("total_points", 0)
        new_points = max(0, old_points + points_to_add)
        
        tier_info = get_citizen_tier(new_points)
        tier_name = tier_info["name"]
        
        updates = {
            "total_points": new_points,
            "tier": tier_name
        }
        citizen_ref.update(updates)

        # Log the points award event
        log_doc = {
            "aadhar_hash": aadhar_hash,
            "rule_key": rule_key,
            "points_awarded": points_to_add,
            "reason": reason,
            "complaint_id": complaint_id,
            "timestamp": now_iso()
        }
        db.collection("gamification_log").add(log_doc)

        return {
            "aadhar_hash": aadhar_hash,
            "new_points": new_points,
            "new_tier": tier_name,
            "points_awarded": points_to_add,
            "rule_key": rule_key
        }
    except Exception as e:
        print(f"⚠️ award_points error: {e}")
        return {"error": str(e)}

def get_leaderboard(limit: int = 10) -> list[dict]:
    """Streams top citizens sorted by total_points descending."""
    try:
        query = db.collection("citizens").stream()
        citizens = [doc.to_dict() for doc in query]
        citizens.sort(key=lambda c: c.get("total_points", 0), reverse=True)
        return citizens[:limit]
    except Exception as e:
        print(f"⚠️ get_leaderboard error: {e}")
        return []

def get_citizen_stats(aadhar_hash: str) -> dict:
    """
    Assembles complete gamification profile for a citizen,
    including progress to the next tier and city-wide rank.
    """
    try:
        doc = db.collection("citizens").document(aadhar_hash).get()
        if not doc.exists:
            return {"error": "Citizen not found"}
        
        citizen = doc.to_dict()
        points = citizen.get("total_points", 0)
        tier_info = get_citizen_tier(points)
        
        # Calculate progress to next tier
        next_tier = "Max Tier"
        progress = 100
        points_needed = 0
        
        # Find index of current tier
        current_idx = -1
        for i, t in enumerate(CIVIC_TIERS):
            if t["name"] == tier_info["name"]:
                current_idx = i
                break
        
        if current_idx != -1 and current_idx < len(CIVIC_TIERS) - 1:
            next_t = CIVIC_TIERS[current_idx + 1]
            next_tier = next_t["name"]
            tier_range = next_t["min"] - tier_info["min"]
            earned = points - tier_info["min"]
            progress = int((earned / tier_range) * 100) if tier_range > 0 else 0
            progress = max(0, min(100, progress))
            points_needed = next_t["min"] - points

        # Find city rank
        all_citizens = get_leaderboard(limit=10000)
        rank = 1
        for idx, c in enumerate(all_citizens):
            if c.get("aadhar_hash") == aadhar_hash:
                rank = idx + 1
                break

        # Fetch point log history
        log_query = db.collection("gamification_log").where("aadhar_hash", "==", aadhar_hash).stream()
        history = [doc.to_dict() for doc in log_query]
        history.sort(key=lambda h: h.get("timestamp", ""), reverse=True)

        return {
            "name": citizen.get("name", ""),
            "points": points,
            "tier": tier_info["name"],
            "badge": tier_info["badge"],
            "color": tier_info["color"],
            "next_tier": next_tier,
            "progress": progress,
            "points_needed": points_needed,
            "rank": rank,
            "strikes": citizen.get("fake_strikes", 0),
            "active": citizen.get("active", True),
            "history": history,
            "total_complaints": citizen.get("total_complaints", 0),
            "resolved_complaints": citizen.get("resolved_complaints", 0)
        }
    except Exception as e:
        print(f"⚠️ get_citizen_stats error: {e}")
        return {"error": str(e)}
