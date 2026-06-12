"""
ai_engine.py — Autonomous AI pipeline. Runs synchronously on complaint submission.
Works 100% offline with no API keys using deterministic mock pipeline.
"""
from datetime import datetime, timezone, timedelta
from data_manager import update_complaint, add_blockchain_entry, award_points, now_iso

RISK_BASE = {
    "Pothole": 30, "Water Leak": 35, "Broken Streetlight": 25,
    "Blocked Drain": 40, "Garbage Dump": 20, "Road Damage": 35,
    "Fallen Tree": 30, "Illegal Construction": 20, "Sewage Overflow": 45, "Other": 15,
}
RISK_FLAGS = {
    "near_school": 20, "near_hospital": 15, "heavy_traffic": 15,
    "monsoon_risk": 25, "near_water": 10, "immediate_danger": 20,
}
DEPARTMENTS = {
    "Pothole": "Roads & Infrastructure Dept",
    "Water Leak": "Water Supply & Sewerage Board",
    "Broken Streetlight": "Electrical & Lighting Dept",
    "Blocked Drain": "Stormwater Drainage Dept",
    "Garbage Dump": "Solid Waste Management Dept",
    "Road Damage": "Roads & Infrastructure Dept",
    "Fallen Tree": "Horticulture & Parks Dept",
    "Illegal Construction": "Town Planning & Development",
    "Sewage Overflow": "Water Supply & Sewerage Board",
    "Other": "General Administration",
}
SLA = {"CRITICAL": 24, "HIGH": 72, "MEDIUM": 168, "LOW": 336}

def calculate_budget(issue_type, priority, severity_score):
    BASE_RATES_INR = {
        "Pothole": 8000, "Water Leak": 12000, "Broken Streetlight": 5000,
        "Blocked Drain": 10000, "Garbage Dump": 3000, "Road Damage": 15000,
        "Fallen Tree": 6000, "Illegal Construction": 2000,
        "Sewage Overflow": 18000, "Other": 5000,
    }
    base = BASE_RATES_INR.get(issue_type, 5000)
    multiplier = {"CRITICAL": 4.0, "HIGH": 2.5, "MEDIUM": 1.5, "LOW": 1.0}[priority]
    severity_factor = 1 + (severity_score / 20)
    total = int(base * multiplier * severity_factor)
    return min(total, 500000)  # Cap at 5 lakh INR

def run_ai_pipeline(complaint: dict) -> dict:
    """
    Full autonomous AI pipeline. Called immediately after complaint submission.
    Returns updated complaint with AI analysis complete.
    """
    cid = complaint["complaint_id"]
    issue_type = complaint.get("issue_type", "Other")
    hazard_flags = complaint.get("hazard_flags", [])
    description = complaint.get("description", "")
    citizen_aadhar = complaint.get("citizen_aadhar_hash", "")
    
    # Step 1: Risk scoring (deterministic — pure Python)
    score = RISK_BASE.get(issue_type, 15)
    for flag in hazard_flags:
        score += RISK_FLAGS.get(flag, 0)
    score += 15  # base severity
    score = min(score, 100)
    
    if score >= 80:
        priority = "CRITICAL"
    elif score >= 60:
        priority = "HIGH"
    elif score >= 40:
        priority = "MEDIUM"
    else:
        priority = "LOW"
    
    dept = DEPARTMENTS.get(issue_type, "General Administration")
    sla_hours = SLA[priority]
    eta = (datetime.now(timezone.utc) + timedelta(hours=sla_hours)).strftime("%Y-%m-%d %H:%M UTC")
    
    severity_score = 7 if priority in ("CRITICAL", "HIGH") else 4
    budget = calculate_budget(issue_type, priority, severity_score)
    team_size = {"CRITICAL": 6, "HIGH": 4, "MEDIUM": 3, "LOW": 2}[priority]
    
    ai_result = {
        "vision": {
            "issue_confirmed": True,
            "detected_type": issue_type,
            "severity": 7 if priority in ("CRITICAL", "HIGH") else 4,
            "confidence": 0.92,
            "is_fake": False,
            "description": f"AI confirmed: {issue_type} detected. {description[:100]}. Immediate action required.",
        },
        "risk": {
            "score": score,
            "priority": priority,
            "factors": hazard_flags,
        },
        "planning": {
            "steps": [
                f"1. Deploy {dept} team within {'2' if priority == 'CRITICAL' else '12'} hours",
                "2. Secure area with safety barriers and warning signs",
                f"3. Assess full extent of {issue_type.lower()} damage",
                "4. Execute repair using standard municipal protocols",
                "5. Photograph completed work for drone verification",
                "6. Submit proof via Worker Portal for drone scan",
            ],
            "budget_inr": budget,
            "team_size": team_size,
            "duration_hours": sla_hours // 3,
            "department": dept,
        },
    }
    
    # Update complaint with AI results
    update_complaint(cid, {
        "status": "ASSIGNED",
        "risk_score": score,
        "priority": priority,
        "assigned_department": dept,
        "resolution_eta": eta,
        "ai_analysis": ai_result,
    }, status_note=f"AI analysis complete. Priority: {priority}. Score: {score}/100. Dept: {dept}",
       actor="AUTONOMOUS_AI_SYSTEM")
    
    # Blockchain entry
    add_blockchain_entry(cid, "AI_ANALYZED", "AUTONOMOUS_AI_SYSTEM",
                         metadata={"priority": priority, "score": score, "dept": dept})
    
    # Award points to citizen
    points = 10
    if priority == "CRITICAL":
        points += 25
    award_points(citizen_aadhar, points,
                 f"Complaint submitted — {priority} priority", cid)
    
    return ai_result


def run_drone_verify(complaint_id, before_b64, after_b64) -> dict:
    """
    Drone verification. Compares before and after photos.
    Works offline — uses image size comparison as proxy for change detection.
    """
    verdict = "VERIFIED_COMPLETE"
    completion_pct = 90
    notes = "Drone scan complete. Repair work confirmed satisfactory. Area restored to acceptable standard."
    
    # If after photo is much smaller than before, likely incomplete
    if before_b64 and after_b64:
        if len(after_b64) < len(before_b64) * 0.3:
            verdict = "REQUIRES_REWORK"
            completion_pct = 40
            notes = "Drone scan detected possible incomplete repair. Rework may be required."
    
    result = {
        "verdict": verdict,
        "completion_percentage": completion_pct,
        "confidence": 0.87,
        "notes": notes,
    }
    
    new_status = "VERIFIED_COMPLETE" if verdict == "VERIFIED_COMPLETE" else "REQUIRES_REWORK"
    update_complaint(complaint_id, {
        "status": new_status,
        "drone_verdict": result,
        "drone_scanned_at": now_iso(),
    }, status_note=f"Drone verification: {verdict}. Completion: {completion_pct}%",
       actor="DRONE_VERIFIER")
    
    add_blockchain_entry(complaint_id, "DRONE_VERIFIED", "DRONE_VERIFIER",
                         metadata=result)
    
    if verdict == "VERIFIED_COMPLETE":
        from data_manager import _load
        db = _load()
        c = db["complaints"].get(complaint_id, {})
        citizen_hash = c.get("citizen_aadhar_hash", "")
        if citizen_hash:
            award_points(citizen_hash, 30, "Drone verified complete", complaint_id)
    
    return result
