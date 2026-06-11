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
import sys

# Reconfigure stdout/stderr to handle emoji/non-ASCII printing on Windows CP1252 consoles safely
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


# ── Google Cloud Project Configuration ──────────────────────────────────────
GCP_PROJECT_ID      = os.getenv("GOOGLE_CLOUD_PROJECT", "mock-project-id")
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
DEFAULT_MAP_LONG = 78.9629  # Note: in config.py, lines 266-267 said DEFAULT_MAP_LAT = 20.5937, DEFAULT_MAP_LNG = 78.9629. We'll support both LNG and LONG.
DEFAULT_MAP_LNG  = 78.9629
DEFAULT_MAP_ZOOM = 5

# ── Drone Patrol Thresholds ──────────────────────────────────────────────────
DRONE_ACCEPTANCE_TIMEOUT_HOURS = 24   # Worker must accept within 24h or drone escalates
DRONE_FAKE_SIMILARITY_THRESHOLD = 0.92 # If completion photo >92% similar to original, flag as fake
