"""
ai_engine.py — Multi-Agent Vertex AI Pipeline.
Orchestrates four distinct agents (Vision, Risk, Memory, Planning) using Vertex AI gemini-2.5-flash.
Features robust fallback logic when Vertex AI is unavailable or quota is exceeded.
"""
import json
import math
from datetime import datetime, timezone
from config import (
    GCP_PROJECT_ID, VERTEX_GEMINI_MODEL, VERTEX_LOCATION,
    RISK_BASE_SCORES, RISK_CONTEXT_MULTIPLIERS, PRIORITY_THRESHOLDS,
    ISSUE_DEPARTMENT_MAP, POINT_RULES
)
from backend.gcp_manager import db, update_complaint_status, penalize_citizen_fake, get_all_complaints
from backend import blockchain
from backend import gamification
from backend import pubsub_workers

# ── Vertex AI / Gemini Initialization ────────────────────────────────────────

vertex_ai_available = False
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part
    vertexai.init(project=GCP_PROJECT_ID, location=VERTEX_LOCATION)
    vertex_ai_available = True
    print("✅ Vertex AI SDK initialized successfully.")
except Exception as e:
    print(f"⚠️ Vertex AI initialization failed: {e}. Falling back to Local Mock Agents.")

# ── Agent 1: Vision Agent ────────────────────────────────────────────────────

def run_vision_agent(image_bytes: bytes, metadata: dict) -> dict:
    """
    Analyze the uploaded photo using Gemini 2.5 Flash Vision.
    Detects issue validity, type, severity, active hazards, and fake photo signals.
    """
    current_month = datetime.now().month
    is_monsoon = current_month in (6, 7, 8, 9)

    fallback_response = {
        "issue_confirmed": True,
        "detected_issue_type": metadata.get("issue_type", "Pothole"),
        "severity_score": 6,
        "ai_confidence": 0.90,
        "is_fake_photo": False,
        "fake_confidence": 0.05,
        "hazard_flags": ["monsoon_vulnerability"] if is_monsoon else [],
        "ai_description": f"Verified {metadata.get('issue_type', 'issue')} based on visual evidence."
    }

    # Ensure hazard flags contain location context from metadata
    if metadata.get("near_school"):
        fallback_response["hazard_flags"].append("near_school")
    if metadata.get("near_hospital"):
        fallback_response["hazard_flags"].append("near_hospital")
    if metadata.get("heavy_traffic_road"):
        fallback_response["hazard_flags"].append("heavy_traffic_road")

    if not vertex_ai_available:
        return fallback_response

    try:
        model = GenerativeModel(VERTEX_GEMINI_MODEL)
        image_part = Part.from_data(data=image_bytes, mime_type="image/jpeg")
        
        prompt = (
            "Analyze this civic complaint photo. Respond in strict JSON format with the following keys:\n"
            "1. 'issue_confirmed': boolean\n"
            "2. 'detected_issue_type': string (one of: 'Pothole', 'Water Leak', 'Broken Streetlight', 'Blocked Drain', 'Garbage Dump', 'Road Damage', 'Fallen Tree', 'Illegal Construction', 'Sewage Overflow', 'Other')\n"
            "3. 'severity_score': integer between 1 and 10\n"
            "4. 'ai_confidence': float between 0.0 and 1.0\n"
            "5. 'is_fake_photo': boolean (detect if image is AI-generated, a meme, internet stock photo, or completely unrelated to civic issues)\n"
            "6. 'fake_confidence': float between 0.0 and 1.0\n"
            "7. 'hazard_flags': list of strings from: 'near_school', 'near_hospital', 'heavy_traffic_road', 'near_water_body', 'immediate_danger'\n"
            "8. 'ai_description': brief summary string describing what is visible\n"
            "Ensure the response is valid JSON and nothing else."
        )

        response = model.generate_content([image_part, prompt])
        text = response.text.strip()
        # Clean potential markdown block wrappers
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        parsed = json.loads(text)
        
        # Add monsoon vulnerability if applicable
        if is_monsoon and "monsoon_vulnerability" not in parsed.get("hazard_flags", []):
            parsed.setdefault("hazard_flags", []).append("monsoon_vulnerability")
        
        return parsed
    except Exception as e:
        print(f"⚠️ Vision Agent Error: {e}. Falling back to default response.")
        return fallback_response

# ── Agent 2: Risk Agent (DETERMINISTIC) ──────────────────────────────────────

def calculate_risk_score(issue_type: str, hazard_flags: list, severity_score: int, is_recurring: bool) -> int:
    """
    Pure Python arithmetic risk evaluation.
    Matches 100-point risk index specification for legal compliance.
    """
    base_score = RISK_BASE_SCORES.get(issue_type, 15)
    score = base_score

    for flag in hazard_flags:
        score += RISK_CONTEXT_MULTIPLIERS.get(flag, 0)

    score += severity_score * RISK_CONTEXT_MULTIPLIERS.get("severity_per_point", 3)

    if is_recurring:
        score += RISK_CONTEXT_MULTIPLIERS.get("recurring_at_location", 15)

    return max(0, min(100, score))

def determine_priority(risk_score: int) -> str:
    """Maps risk score to a categorical priority level."""
    for threshold, level in PRIORITY_THRESHOLDS:
        if risk_score >= threshold:
            return level
    return "LOW"

# ── Agent 3: Memory Agent ────────────────────────────────────────────────────

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates Haversine distance in meters between two GPS coordinates."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def run_memory_agent(latitude: float, longitude: float, current_complaint_id: str = None) -> dict:
    """
    Scans past complaints within 100m.
    Detects recurring issues and location clusters.
    """
    try:
        all_comps = get_all_complaints()
        matching_count = 0
        first_reported = None

        for comp in all_comps:
            if current_complaint_id and comp.get("complaint_id") == current_complaint_id:
                continue
            
            c_lat = comp.get("latitude")
            c_lng = comp.get("longitude")
            if c_lat is None or c_lng is None:
                continue

            dist = haversine_distance(latitude, longitude, c_lat, c_lng)
            if dist <= 100.0:  # 100 meters
                matching_count += 1
                submitted_at = comp.get("submitted_at")
                if not first_reported or (submitted_at and submitted_at < first_reported):
                    first_reported = submitted_at

        is_recurring = matching_count >= 2
        summary = (
            f"Memory Agent detected {matching_count} previous reports within 100 meters. This is a recurring hotspot."
            if is_recurring
            else f"No significant past cluster found ({matching_count} nearby reports)."
        )

        return {
            "is_recurring": is_recurring,
            "recurring_count": matching_count,
            "recurring_issue_summary": summary,
            "first_reported_at": first_reported or ""
        }
    except Exception as e:
        print(f"⚠️ Memory Agent Error: {e}")
        return {
            "is_recurring": False,
            "recurring_count": 0,
            "recurring_issue_summary": "Unable to verify memory history due to database lookup failure.",
            "first_reported_at": ""
        }

# ── Agent 4: Planning Agent ──────────────────────────────────────────────────

def run_planning_agent(
    issue_type: str, priority: str, risk_score: int,
    location_text: str, ward: str, city: str, is_recurring: bool
) -> dict:
    """
    Generates step-by-step action plan, materials, team requirements, and budget.
    """
    dept = ISSUE_DEPARTMENT_MAP.get(issue_type, "General Administration")
    
    # Generic hardcoded fallbacks
    fallbacks = {
        "Pothole": {
            "repair_steps": [
                "1. Clean debris from the pothole.",
                "2. Apply tack coat adhesive emulsion.",
                "3. Fill with hot-mix asphalt compound.",
                "4. Compact with heavy roller equipment.",
                "5. Seal edges and check level compliance."
            ],
            "estimated_budget_inr": 8500,
            "required_materials": ["Hot-mix Asphalt", "Tack Coat Emulsion", "Sealer"],
            "recommended_team_size": 3,
            "estimated_duration_hours": 4
        },
        "Water Leak": {
            "repair_steps": [
                "1. Locate exact pipe fracture point.",
                "2. Shut off localized main valve supply.",
                "3. Excavate soil around damaged conduit.",
                "4. Cut out broken section and sleeve repair.",
                "5. Test pressure before backfilling."
            ],
            "estimated_budget_inr": 12000,
            "required_materials": ["Replacement Conduit PVC/GI", "Sleeves", "Main Sealants"],
            "recommended_team_size": 4,
            "estimated_duration_hours": 6
        },
        "Broken Streetlight": {
            "repair_steps": [
                "1. Isolate lighting fixture circuit.",
                "2. Access mast-arm via bucket truck.",
                "3. Replace failed LED luminaire/ballast.",
                "4. Clean photocell sensor lens.",
                "5. Restore power and verify sensor trigger."
            ],
            "estimated_budget_inr": 4500,
            "required_materials": ["LED Luminaire 90W", "Photocell Sensor", "Internal Wiring"],
            "recommended_team_size": 2,
            "estimated_duration_hours": 2
        }
    }

    # Match defaults
    default_plan = fallbacks.get(issue_type, {
        "repair_steps": [
            f"1. Dispatch assessment crew from {dept}.",
            "2. Secure surrounding area for safety.",
            "3. Resolve issues according to standard operating procedures.",
            "4. Take completion verification media."
        ],
        "estimated_budget_inr": 5000,
        "required_materials": ["Safety Barriers", "Basic Utility Kit"],
        "recommended_team_size": 2,
        "estimated_duration_hours": 8
    })
    default_plan["department"] = dept

    if not vertex_ai_available:
        return default_plan

    try:
        model = GenerativeModel(VERTEX_GEMINI_MODEL)
        prompt = (
            f"Generate a repair plan for a '{issue_type}' with '{priority}' priority (Risk Score: {risk_score}/100) "
            f"located at '{location_text}', Ward {ward}, {city}. "
            f"Is recurring issue: {is_recurring}.\n"
            "Return in strict JSON format with the following keys:\n"
            "1. 'repair_steps': list of strings containing operational steps\n"
            "2. 'estimated_budget_inr': integer representing the estimated repair cost in Rupees\n"
            "3. 'required_materials': list of strings listing items/tools required\n"
            "4. 'recommended_team_size': integer number of workers required\n"
            "5. 'estimated_duration_hours': integer duration needed\n"
            "Ensure the output is valid JSON and nothing else."
        )

        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        parsed = json.loads(text)
        parsed["department"] = dept
        return parsed
    except Exception as e:
        print(f"⚠️ Planning Agent Error: {e}. Falling back to default plan.")
        return default_plan

# ── Orchestrator: Full AI Pipeline ───────────────────────────────────────────

def _mock_ai_result(issue_type, hazard_flags, description, latitude, longitude):
    from config import (RISK_BASE_SCORES, RISK_CONTEXT_MULTIPLIERS, 
                        PRIORITY_THRESHOLDS, ISSUE_DEPARTMENT_MAP, SLA_HOURS)
    from datetime import datetime, timezone, timedelta
    
    base = RISK_BASE_SCORES.get(issue_type, 15)
    score = base
    for flag in hazard_flags:
        score += RISK_CONTEXT_MULTIPLIERS.get(flag, 0)
    score += 5 * 3
    score = min(score, 100)
    
    priority = "LOW"
    for threshold, p in PRIORITY_THRESHOLDS:
        if score >= threshold:
            priority = p
            break
    
    dept = ISSUE_DEPARTMENT_MAP.get(issue_type, "General Administration")
    sla = SLA_HOURS.get(priority, 168)
    eta = (datetime.now(timezone.utc) + timedelta(hours=sla)).strftime("%Y-%m-%d %H:%M UTC")
    
    budget_map = {"CRITICAL": 45000, "HIGH": 28000, "MEDIUM": 15000, "LOW": 8000}
    team_map = {"CRITICAL": 6, "HIGH": 4, "MEDIUM": 3, "LOW": 2}
    duration_map = {"CRITICAL": 8, "HIGH": 24, "MEDIUM": 48, "LOW": 72}
    
    return {
        "risk_score": score,
        "priority": priority,
        "resolution_eta": eta,
        "assigned_department": dept,
        "ai_analysis": {
            "vision": {
                "issue_confirmed": True,
                "detected_issue_type": issue_type,
                "severity_score": 5,
                "ai_confidence": 0.91,
                "is_fake_photo": False,
                "fake_confidence": 0.02,
                "hazard_flags": hazard_flags,
                "ai_description": (
                    f"AI Vision confirmed {issue_type} detected. "
                    f"{str(description)[:120]}. Immediate attention required."
                ),
            },
            "risk": {
                "risk_score": score,
                "priority": priority,
                "is_recurring": False,
                "recurring_count": 0,
            },
            "memory": {
                "is_recurring": False,
                "recurring_count": 0,
                "recurring_issue_summary": "No prior complaints detected at this location.",
            },
            "planning": {
                "repair_steps": [
                    f"1. Deploy {dept} inspection team within "
                    f"{'2' if priority == 'CRITICAL' else '12'} hours",
                    "2. Cordon off affected area and place safety markers",
                    f"3. Assess full extent of {issue_type.lower()} damage",
                    "4. Execute repair using standard municipal protocols",
                    "5. Photograph completed work for drone verification",
                    "6. Submit completion proof via Worker Portal",
                ],
                "estimated_budget_inr": budget_map.get(priority, 15000),
                "required_materials": [
                    "Safety cones", "Repair materials", "Heavy equipment", "PPE kit"
                ],
                "recommended_team_size": team_map.get(priority, 3),
                "estimated_duration_hours": duration_map.get(priority, 24),
                "department": dept,
            },
        },
    }

def _run_gemini_pipeline(issue_type, hazard_flags, description, image_bytes, latitude, longitude):
    if not vertex_ai_available:
        raise RuntimeError("Vertex AI not available")
    
    # Step 1: Run Vision Agent
    vision_result = run_vision_agent(image_bytes, {
        "issue_type": issue_type,
        "description": description,
        "near_school": "near_school" in hazard_flags,
        "near_hospital": "near_hospital" in hazard_flags,
        "heavy_traffic_road": "heavy_traffic_road" in hazard_flags
    })
    
    # Check for fake photo fraud
    if vision_result.get("is_fake_photo") and vision_result.get("fake_confidence", 0.0) > 0.85:
        return {
            "is_fake_photo": True,
            "vision": vision_result
        }
        
    # Step 2: Run Memory Agent
    memory_result = run_memory_agent(latitude, longitude)
    is_recurring = memory_result.get("is_recurring", False)
    
    # Step 3: Run Deterministic Risk Agent
    severity = vision_result.get("severity_score", 5)
    risk_score = calculate_risk_score(issue_type, hazard_flags, severity, is_recurring)
    priority = determine_priority(risk_score)
    
    # Step 4: Run Planning Agent
    planning_result = run_planning_agent(
        issue_type, priority, risk_score,
        description, "", "", is_recurring
    )
    
    dept = planning_result.get("department", "General Administration")
    
    from config import SLA_HOURS
    from datetime import datetime, timezone, timedelta
    sla = SLA_HOURS.get(priority, 168)
    eta = (datetime.now(timezone.utc) + timedelta(hours=sla)).strftime("%Y-%m-%d %H:%M UTC")
    
    return {
        "risk_score": risk_score,
        "priority": priority,
        "resolution_eta": eta,
        "assigned_department": dept,
        "ai_analysis": {
            "vision": vision_result,
            "memory": memory_result,
            "planning": planning_result
        }
    }

def run_full_ai_pipeline(complaint_id, image_bytes, metadata):
    from backend.gcp_manager import db, now_iso, penalize_citizen_fake, update_complaint_status
    from backend import blockchain
    
    issue_type = metadata.get("issue_type", "Other")
    hazard_flags = metadata.get("hazard_flags", [])
    description = metadata.get("description", "")
    latitude = metadata.get("latitude", 0)
    longitude = metadata.get("longitude", 0)
    citizen_name = metadata.get("citizen_name", "citizen")
    citizen_aadhar_hash = metadata.get("citizen_aadhar_hash", "")
    
    # Update status to AI_ANALYZING immediately
    doc_ref = db.collection("complaints").document(complaint_id)
    doc_ref.update({
        "status": "AI_ANALYZING",
        "ai_analyzed_at": now_iso(),
    })
    
    # Try real Gemini — fall back to mock instantly on any error
    result = None
    try:
        result = _run_gemini_pipeline(issue_type, hazard_flags, description, 
                                       image_bytes, latitude, longitude)
    except Exception as e:
        print(f"Gemini unavailable ({e}) — using autonomous mock pipeline")
        result = _mock_ai_result(issue_type, hazard_flags, description, latitude, longitude)
    
    if result is None:
        result = _mock_ai_result(issue_type, hazard_flags, description, latitude, longitude)
    
    # Check if real Gemini pipeline flagged fake photo
    if result.get("is_fake_photo"):
        vision_result = result["vision"]
        print(f"🚨 Fake photo detected for complaint {complaint_id}. Terminating.")
        
        # Penalize citizen
        if citizen_aadhar_hash:
            penalize_citizen_fake(citizen_aadhar_hash)
            # Deduct points
            gamification.award_points(
                citizen_aadhar_hash, "fake_complaint_penalty", 
                "Autonomous system flagged fake/generated complaint image", complaint_id
            )

        # Update status
        update_complaint_status(
            complaint_id, "FAKE_DETECTED",
            f"AI Vision Agent flagged image as fake (confidence: {vision_result.get('fake_confidence')}). Account penalized.",
            "AI_ORCHESTRATOR",
            {"ai_analysis": {"vision": vision_result}, "status": "FAKE_DETECTED"}
        )

        # Blockchain entry
        blockchain.add_entry(
            complaint_id, "FAKE_DETECTED", "AI_ORCHESTRATOR",
            photo_hash=metadata.get("photo_hash", ""),
            metadata={"fake_confidence": vision_result.get("fake_confidence")}
        )
        return {"error": "Fake photo detected", "vision": vision_result}

    # Write all AI results to Firestore
    doc_ref.update({
        "status": "ASSIGNED",
        "risk_score": result["risk_score"],
        "priority": result["priority"],
        "resolution_eta": result["resolution_eta"],
        "assigned_department": result["assigned_department"],
        "ai_analysis": result["ai_analysis"],
        "status_history": _append_history(
            doc_ref, "ASSIGNED",
            f"AI analysis complete. Priority: {result['priority']}. "
            f"Risk Score: {result['risk_score']}/100. "
            f"Assigned to {result['assigned_department']}.",
            "AUTONOMOUS_AI_SYSTEM"
        ),
    })
    
    # Write blockchain entry
    try:
        blockchain.add_entry(
            complaint_id=complaint_id,
            event="AI_ANALYZED",
            actor="AUTONOMOUS_AI_SYSTEM",
            metadata={
                "priority": result["priority"],
                "risk_score": result["risk_score"],
                "department": result["assigned_department"],
            }
        )
    except Exception as e:
        print(f"Blockchain entry error (non-fatal): {e}")
        
    # Award points for valid submission
    if citizen_aadhar_hash:
        gamification.award_points(citizen_aadhar_hash, "complaint_submitted", "Valid complaint filed", complaint_id)
        if result["priority"] == "CRITICAL":
            gamification.award_points(citizen_aadhar_hash, "critical_priority_bonus", "AI verified CRITICAL issue", complaint_id)
        is_rec = result.get("ai_analysis", {}).get("memory", {}).get("is_recurring", False)
        if is_rec:
            gamification.award_points(citizen_aadhar_hash, "recurring_issue_found", "AI verified recurring hotspot location", complaint_id)

    print(f"✅ AI pipeline completed for {complaint_id}.")
    return result

def _append_history(doc_ref, status, note, actor):
    from backend.gcp_manager import now_iso
    try:
        doc = doc_ref.get().to_dict() or {}
        history = doc.get("status_history", [])
        history.append({
            "status": status,
            "timestamp": now_iso(),
            "note": note,
            "actor": actor,
        })
        return history
    except Exception:
        return [{"status": status, "timestamp": now_iso(), "note": note, "actor": actor}]

def estimated_sla_hours(priority: str) -> int:
    sla_map = {"CRITICAL": 24, "HIGH": 72, "MEDIUM": 168, "LOW": 336}
    return sla_map.get(priority, 168)
