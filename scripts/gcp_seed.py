"""
gcp_seed.py — Idempotent developer/demo database seeder.
Seeds citizens, workers, active and resolved complaints, blockchain ledger entries,
and autonomous drone-filed management complaints. Nagpur, Pune, Mumbai geographic anchors.
"""
import sys
import os
from datetime import datetime, timedelta, timezone

# Add parent directory to path to allow running directly from this folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ISSUE_TYPES, COMPLAINT_STATUSES, CIVIC_TIERS, GCP_PROJECT_ID
from backend.gcp_manager import db, hash_identifier, hash_file_bytes, now_iso
from backend import blockchain

def seed_db() -> None:
    print("🌱 Starting idempotent database seeding sweep...")
    
    # 1. Citizens Seeding (5 citizens)
    citizens_data = [
        {
            "name": "Rohan Deshmukh",
            "phone": "9876543210",
            "aadhar": "111122223333",
            "city": "Nagpur",
            "ward": "Ward 12",
            "total_points": 450,
            "tier": "🥇 Gold Champion"
        },
        {
            "name": "Priya Sharma",
            "phone": "9876543211",
            "aadhar": "444455556666",
            "city": "Pune",
            "ward": "Ward 5",
            "total_points": 180,
            "tier": "🥈 Silver Guardian"
        },
        {
            "name": "Amit Patel",
            "phone": "9876543212",
            "aadhar": "777788889999",
            "city": "Mumbai",
            "ward": "Ward 22",
            "total_points": 45,
            "tier": "🥉 Bronze Citizen"
        },
        {
            "name": "Siddharth Rao",
            "phone": "9876543213",
            "aadhar": "121234345656",
            "city": "Bengaluru",
            "ward": "Ward 8",
            "total_points": 750,
            "tier": "💎 Platinum Sentinel"
        },
        {
            "name": "Ananya Sen",
            "phone": "9876543214",
            "aadhar": "909080807070",
            "city": "Delhi",
            "ward": "Ward 14",
            "total_points": 1200,
            "tier": "🏆 Diamond Legend"
        }
    ]

    seeded_citizens = {}
    for c in citizens_data:
        a_hash = hash_identifier(c["aadhar"])
        p_hash = hash_identifier(c["phone"], salt="phone_salt_v1")
        doc_ref = db.collection("citizens").document(a_hash)
        
        if doc_ref.get().exists:
            print(f"⏭️ Skipped: Citizen '{c['name']}' already exists")
            seeded_citizens[c["aadhar"]] = a_hash
            continue
            
        payload = {
            "aadhar_hash": a_hash,
            "phone_hash": p_hash,
            "phone_display": c["phone"][-4:].rjust(10, "*"),
            "name": c["name"],
            "city": c["city"],
            "ward": c["ward"],
            "registered_at": now_iso(),
            "active": True,
            "fake_strikes": 0,
            "total_points": c["total_points"],
            "tier": c["tier"],
            "total_complaints": 3,
            "resolved_complaints": 2
        }
        doc_ref.set(payload)
        seeded_citizens[c["aadhar"]] = a_hash
        print(f"✅ Seeded: Citizen '{c['name']}'")

    # 2. Workers Seeding (5 workers)
    workers_data = [
        {
            "worker_id": "WRK-NAG-01",
            "name": "Vidarbha Infra Repairs",
            "city": "Nagpur",
            "avg_rating": 4.6,
            "completed_jobs": 15,
            "total_ratings": 15,
            "rating_sum": 69.0,
            "penalty_count": 0,
            "performance_flag": "PREFERRED",
            "active": True
        },
        {
            "worker_id": "WRK-PUN-02",
            "name": "Pune City Utilities",
            "city": "Pune",
            "avg_rating": 4.1,
            "completed_jobs": 10,
            "total_ratings": 10,
            "rating_sum": 41.0,
            "penalty_count": 1,
            "performance_flag": "STANDARD",
            "active": True
        },
        {
            "worker_id": "WRK-MUM-03",
            "name": "Apex Sanitation Ltd",
            "city": "Mumbai",
            "avg_rating": 3.8,
            "completed_jobs": 8,
            "total_ratings": 8,
            "rating_sum": 30.4,
            "penalty_count": 0,
            "performance_flag": "STANDARD",
            "active": True
        },
        {
            "worker_id": "WRK-BLR-04",
            "name": "Bengaluru Road Solutions",
            "city": "Bengaluru",
            "avg_rating": 3.2,
            "completed_jobs": 6,
            "total_ratings": 6,
            "rating_sum": 19.2,
            "penalty_count": 2,
            "performance_flag": "STANDARD",
            "active": True
        },
        {
            "worker_id": "WRK-DEL-05",
            "name": "Capital Civic Builders",
            "city": "Delhi",
            "avg_rating": 2.1,
            "completed_jobs": 5,
            "total_ratings": 5,
            "rating_sum": 10.5,
            "penalty_count": 3,
            "performance_flag": "REVIEW_REQUIRED",
            "active": True
        }
    ]

    for w in workers_data:
        doc_ref = db.collection("workers").document(w["worker_id"])
        if doc_ref.get().exists:
            print(f"⏭️ Skipped: Worker '{w['worker_id']}' already exists")
            continue
        doc_ref.set(w)
        print(f"✅ Seeded: Worker '{w['worker_id']}'")

    # 3. Complaints Seeding (15 complaints across Nagpur, Pune, Mumbai, Bengaluru, Delhi)
    complaints_data = [
        # Nagpur
        {
            "id": "CS-NAG-001",
            "issue_type": "Pothole",
            "description": "Massive 2-meter wide pothole near main crossroad. Dangerous for motorbikes.",
            "loc_text": "Badnera Road, Nagpur Highway Cluster",
            "lat": 20.9255, "lng": 77.7663,
            "city": "Nagpur", "ward": "Ward 12",
            "citizen_idx": 0, "status": "VERIFIED_COMPLETE", "priority": "CRITICAL",
            "assigned_worker": "WRK-NAG-01"
        },
        {
            "id": "CS-NAG-002",
            "issue_type": "Water Leak",
            "description": "Drinking water pipeline leakage spraying water continuously.",
            "loc_text": "Ramdaspeth Hospital Belt",
            "lat": 21.1396, "lng": 79.0805,
            "city": "Nagpur", "ward": "Ward 12",
            "citizen_idx": 0, "status": "IN_PROGRESS", "priority": "HIGH",
            "assigned_worker": "WRK-NAG-01"
        },
        {
            "id": "CS-NAG-003",
            "issue_type": "Broken Streetlight",
            "description": "Street light has been non-functional for 3 weeks. Area is dark and unsafe.",
            "loc_text": "Amravati Road near petrol pump",
            "lat": 21.1504, "lng": 79.0266,
            "city": "Nagpur", "ward": "Ward 12",
            "citizen_idx": 0, "status": "ASSIGNED", "priority": "MEDIUM",
            "assigned_worker": "WRK-NAG-01"
        },
        # Pune
        {
            "id": "CS-PUN-001",
            "issue_type": "Blocked Drain",
            "description": "Stormwater drain is completely choked with plastic garbage.",
            "loc_text": "Kothrud Depot Circle",
            "lat": 18.5074, "lng": 73.8077,
            "city": "Pune", "ward": "Ward 5",
            "citizen_idx": 1, "status": "ACCEPTED", "priority": "HIGH",
            "assigned_worker": "WRK-PUN-02"
        },
        {
            "id": "CS-PUN-002",
            "issue_type": "Garbage Dump",
            "description": "Illegal dump piling up behind vegetable market. Heavy smell.",
            "loc_text": "Hadapsar Main Bazar Road",
            "lat": 18.5089, "lng": 73.9259,
            "city": "Pune", "ward": "Ward 5",
            "citizen_idx": 1, "status": "PENDING", "priority": "MEDIUM",
            "assigned_worker": None
        },
        {
            "id": "CS-PUN-003",
            "issue_type": "Road Damage",
            "description": "Asphalt top layer completely worn out. Hard to drive.",
            "loc_text": "Baner Highway exit lane",
            "lat": 18.5590, "lng": 73.7797,
            "city": "Pune", "ward": "Ward 5",
            "citizen_idx": 1, "status": "VERIFIED_COMPLETE", "priority": "HIGH",
            "assigned_worker": "WRK-PUN-02"
        },
        # Mumbai
        {
            "id": "CS-MUM-001",
            "issue_type": "Sewage Overflow",
            "description": "Open sewer manhole overflowing directly onto pedestrian sidewalk.",
            "loc_text": "Dadar Station East Junction",
            "lat": 19.0178, "lng": 72.8478,
            "city": "Mumbai", "ward": "Ward 22",
            "citizen_idx": 2, "status": "IN_PROGRESS", "priority": "CRITICAL",
            "assigned_worker": "WRK-MUM-03"
        },
        {
            "id": "CS-MUM-002",
            "issue_type": "Fallen Tree",
            "description": "Large branch fell and blocked residential lane traffic.",
            "loc_text": "Andheri West SV Road corner",
            "lat": 19.1136, "lng": 72.8697,
            "city": "Mumbai", "ward": "Ward 22",
            "citizen_idx": 2, "status": "ASSIGNED", "priority": "LOW",
            "assigned_worker": "WRK-MUM-03"
        },
        {
            "id": "CS-MUM-003",
            "issue_type": "Illegal Construction",
            "description": "Commercial block building extending stalls onto public footpath.",
            "loc_text": "Bandra Linking Road",
            "lat": 19.0583, "lng": 72.8302,
            "city": "Mumbai", "ward": "Ward 22",
            "citizen_idx": 2, "status": "PENDING", "priority": "MEDIUM",
            "assigned_worker": None
        },
        # Bengaluru
        {
            "id": "CS-BLR-001",
            "issue_type": "Water Leak",
            "description": "Water pipe burst in public park, flooding pathways.",
            "loc_text": "Indiranagar 80 Feet Road Park",
            "lat": 12.9719, "lng": 77.6412,
            "city": "Bengaluru", "ward": "Ward 8",
            "citizen_idx": 3, "status": "ESCALATED", "priority": "HIGH",
            "assigned_worker": "WRK-BLR-04"
        },
        {
            "id": "CS-BLR-002",
            "issue_type": "Pothole",
            "description": "Series of deep potholes on turning lane.",
            "loc_text": "Silk Board Flyover Ramp",
            "lat": 12.9176, "lng": 77.6244,
            "city": "Bengaluru", "ward": "Ward 8",
            "citizen_idx": 3, "status": "VERIFIED_COMPLETE", "priority": "CRITICAL",
            "assigned_worker": "WRK-BLR-04"
        },
        {
            "id": "CS-BLR-003",
            "issue_type": "Blocked Drain",
            "description": "Water logging on road due to blocked drains during afternoon showers.",
            "loc_text": "Koramangala 3rd Block",
            "lat": 12.9343, "lng": 77.6210,
            "city": "Bengaluru", "ward": "Ward 8",
            "citizen_idx": 3, "status": "PENDING", "priority": "MEDIUM",
            "assigned_worker": None
        },
        # Delhi
        {
            "id": "CS-DEL-001",
            "issue_type": "Sewage Overflow",
            "description": "Severe drainage backup flooding basement entryways.",
            "loc_text": "Connaught Place Block A",
            "lat": 28.6304, "lng": 77.2177,
            "city": "Delhi", "ward": "Ward 14",
            "citizen_idx": 4, "status": "ESCALATED", "priority": "CRITICAL",
            "assigned_worker": "WRK-DEL-05"
        },
        {
            "id": "CS-DEL-002",
            "issue_type": "Broken Streetlight",
            "description": "Entire lane streetlights are blacked out.",
            "loc_text": "Karol Bagh Market Lane",
            "lat": 28.6441, "lng": 77.1882,
            "city": "Delhi", "ward": "Ward 14",
            "citizen_idx": 4, "status": "VERIFIED_COMPLETE", "priority": "HIGH",
            "assigned_worker": "WRK-DEL-05"
        },
        {
            "id": "CS-DEL-003",
            "issue_type": "Garbage Dump",
            "description": "Massive pile of solid waste dumped on corner lot.",
            "loc_text": "Lajpat Nagar Ring Road",
            "lat": 28.5683, "lng": 77.2410,
            "city": "Delhi", "ward": "Ward 14",
            "citizen_idx": 4, "status": "PENDING", "priority": "LOW",
            "assigned_worker": None
        }
    ]

    p_hash = hash_file_bytes(b"dummy_seed_photo_bytes")

    for index, c in enumerate(complaints_data):
        doc_ref = db.collection("complaints").document(c["id"])
        if doc_ref.get().exists:
            print(f"⏭️ Skipped: Complaint '{c['id']}' already exists")
            continue

        c_aadhar_hash = citizens_data[c["citizen_idx"]]["aadhar"]
        c_aadhar_hash = hash_identifier(c_aadhar_hash)
        c_name = citizens_data[c["citizen_idx"]]["name"]
        c_phone = citizens_data[c["citizen_idx"]]["phone"]
        c_phone_display = c_phone[-4:].rjust(10, "*")

        submitted_at_dt = datetime.now(timezone.utc) - timedelta(days=5 - (index % 3))
        submitted_at = submitted_at_dt.isoformat()

        # Build complaint doc
        comp_doc = {
            "complaint_id": c["id"],
            "citizen_aadhar_hash": c_aadhar_hash,
            "citizen_name": c_name,
            "citizen_phone_display": c_phone_display,
            "city": c["city"],
            "ward": c["ward"],
            "issue_type": c["issue_type"],
            "description": c["description"],
            "location_text": c["loc_text"],
            "latitude": c["lat"],
            "longitude": c["lng"],
            "photo_path": f"gs://{GCP_PROJECT_ID}-civic-media/complaints/{c['id']}/original.jpg",
            "photo_hash": p_hash,
            "completion_photo_path": f"gs://{GCP_PROJECT_ID}-civic-media/complaints/{c['id']}/completion.jpg" if c["status"] in ("VERIFIED_COMPLETE", "CLOSED") else None,
            "completion_photo_hash": p_hash if c["status"] in ("VERIFIED_COMPLETE", "CLOSED") else None,
            "submitted_at": submitted_at,
            "ai_analyzed_at": (submitted_at_dt + timedelta(seconds=15)).isoformat(),
            "assigned_at": (submitted_at_dt + timedelta(hours=2)).isoformat() if c["assigned_worker"] else None,
            "accepted_at": (submitted_at_dt + timedelta(hours=3)).isoformat() if c["status"] in ("ACCEPTED", "IN_PROGRESS", "VERIFIED_COMPLETE", "CLOSED", "ESCALATED") and c["assigned_worker"] else None,
            "work_started_at": (submitted_at_dt + timedelta(hours=6)).isoformat() if c["status"] in ("IN_PROGRESS", "VERIFIED_COMPLETE", "CLOSED") and c["assigned_worker"] else None,
            "completion_uploaded_at": (submitted_at_dt + timedelta(days=1)).isoformat() if c["status"] in ("VERIFIED_COMPLETE", "CLOSED") else None,
            "drone_scanned_at": (submitted_at_dt + timedelta(days=1, hours=1)).isoformat() if c["status"] in ("VERIFIED_COMPLETE", "CLOSED") else None,
            "citizen_rated_at": (submitted_at_dt + timedelta(days=1, hours=2)).isoformat() if c["status"] == "CLOSED" else None,
            "resolved_at": (submitted_at_dt + timedelta(days=1, hours=1)).isoformat() if c["status"] in ("VERIFIED_COMPLETE", "CLOSED") else None,
            "assigned_worker_id": c["assigned_worker"],
            "assigned_department": ISSUE_TYPES[0], # Defaults
            "ai_analysis": {
                "vision": {
                    "issue_confirmed": True,
                    "detected_issue_type": c["issue_type"],
                    "severity_score": 6 if c["priority"] == "HIGH" else 9 if c["priority"] == "CRITICAL" else 4,
                    "ai_confidence": 0.94,
                    "is_fake_photo": False,
                    "fake_confidence": 0.02,
                    "hazard_flags": [],
                    "ai_description": f"AI visual audit confirms a {c['issue_type']} blocking public space."
                },
                "memory": {
                    "is_recurring": False,
                    "recurring_count": 0,
                    "recurring_issue_summary": "No matching spatial clusters.",
                    "first_reported_at": ""
                },
                "planning": {
                    "repair_steps": [
                        "1. Excavate surrounding gravel overlay.",
                        "2. Pour reinforced concrete aggregate cement.",
                        "3. Level and inspect compliance margins."
                    ],
                    "estimated_budget_inr": 7500,
                    "required_materials": ["Reinforced Cement", "Aggregate Gravel"],
                    "recommended_team_size": 3,
                    "estimated_duration_hours": 8,
                    "department": "Infrastructure & Roads Board"
                }
            },
            "risk_score": 85 if c["priority"] == "CRITICAL" else 65 if c["priority"] == "HIGH" else 45 if c["priority"] == "MEDIUM" else 25,
            "priority": c["priority"],
            "resolution_eta": "Completed" if c["status"] in ("VERIFIED_COMPLETE", "CLOSED") else "Within 48 hours",
            "status": c["status"],
            "drone_verdict": "VERIFIED_COMPLETE" if c["status"] in ("VERIFIED_COMPLETE", "CLOSED") else None,
            "citizen_rating": 5 if c["status"] == "CLOSED" else None,
            "citizen_rating_comment": "Excellent quick repair. Flat finish." if c["status"] == "CLOSED" else None,
            "management_complaint_filed": (c["status"] == "ESCALATED"),
            "is_recurring": False,
            "recurring_count": 0,
            "status_history": [
                {
                    "status": "PENDING",
                    "timestamp": submitted_at,
                    "note": "Complaint filed. AI analysis queued.",
                    "actor": c_name
                }
            ]
        }
        
        # Populate GCS mock storage with files to ensure mock downloads work
        from backend.gcp_manager import storage_client, MockStorageClient
        if isinstance(storage_client, MockStorageClient):
            bucket = storage_client.bucket(f"{GCP_PROJECT_ID}-civic-media")
            # original photo dummy
            bucket.blob(f"complaints/{c['id']}/original.jpg").upload_from_string(b"dummy_seed_photo_bytes")
            if c["status"] in ("VERIFIED_COMPLETE", "CLOSED"):
                # completion photo dummy
                bucket.blob(f"complaints/{c['id']}/completion.jpg").upload_from_string(b"dummy_seed_photo_bytes")

        # Set doc
        doc_ref.set(comp_doc)
        print(f"✅ Seeded: Complaint '{c['id']}'")

    # 4. Management Complaints Seeding (3 entries)
    m_complaints_data = [
        {
            "id": "MC-NAG-901",
            "complaint_id": "CS-BLR-001",
            "worker_id": "WRK-BLR-04",
            "violation": "SLA_BREACH",
            "evidence": "Worker accepted task but failed to start repairs before the 72-hour SLA deadline for HIGH priority."
        },
        {
            "id": "MC-NAG-902",
            "complaint_id": "CS-DEL-001",
            "worker_id": "WRK-DEL-05",
            "violation": "NON_ACCEPTANCE",
            "evidence": "Contractor failed to accept assignment within the mandated 24-hour response window."
        },
        {
            "id": "MC-NAG-903",
            "complaint_id": "CS-NAG-002",
            "worker_id": "WRK-NAG-01",
            "violation": "FAKE_COMPLETION",
            "evidence": "Drone vision scan flagged identical image upload. Contractor uploaded same photo as complaint."
        }
    ]

    for mc in m_complaints_data:
        doc_ref = db.collection("management_complaints").document(mc["id"])
        if doc_ref.get().exists:
            print(f"⏭️ Skipped: Management Complaint '{mc['id']}' already exists")
            continue
            
        payload_mc = {
            "management_complaint_id": mc["id"],
            "linked_complaint_id": mc["complaint_id"],
            "accused_worker_id": mc["worker_id"],
            "violation_type": mc["violation"],
            "evidence_note": mc["evidence"],
            "filed_by": "DRONE_AUTONOMOUS_SYSTEM",
            "filed_at": now_iso(),
            "status": "OPEN",
            "authority_action": None,
            "authority_action_at": None
        }
        doc_ref.set(payload_mc)
        print(f"✅ Seeded: Management Complaint '{mc['id']}'")

    # 5. Seeding gamification logs
    log_ref = db.collection("gamification_log")
    # Clean/seed check
    log_check = list(log_ref.limit(1).stream())
    if log_check:
        print("⏭️ Skipped: Gamification log already has entries")
    else:
        log_entries = [
            {"aadhar_hash": hash_identifier("111122223333"), "rule_key": "complaint_submitted", "points_awarded": 10, "reason": "Valid complaint submitted", "complaint_id": "CS-NAG-001", "timestamp": now_iso()},
            {"aadhar_hash": hash_identifier("111122223333"), "rule_key": "critical_priority_bonus", "points_awarded": 25, "reason": "System categorized as CRITICAL priority", "complaint_id": "CS-NAG-001", "timestamp": now_iso()},
            {"aadhar_hash": hash_identifier("444455556666"), "rule_key": "complaint_submitted", "points_awarded": 10, "reason": "Valid complaint submitted", "complaint_id": "CS-PUN-001", "timestamp": now_iso()},
            {"aadhar_hash": hash_identifier("909080807070"), "rule_key": "drone_verified_complete", "points_awarded": 30, "reason": "Drone verified repair completed", "complaint_id": "CS-DEL-002", "timestamp": now_iso()}
        ]
        for entry in log_entries:
            log_ref.add(entry)
        print("✅ Seeded: Gamification activity logs")

    # 6. Blockchain ledger hash linking seed (20 sequential blocks)
    # Check if blockchain already seeded
    ledger_ref = db.collection("blockchain_ledger")
    ledger_check = list(ledger_ref.limit(1).stream())
    if ledger_check:
        print("⏭️ Skipped: Blockchain ledger already seeded")
    else:
        # Seed 20 hash-linked blocks sequentially
        print("🔗 Writing 20 sequentially linked blocks to Blockchain Ledger...")
        blockchain.add_entry("CS-NAG-001", "COMPLAINT_SUBMITTED", "Rohan Deshmukh", p_hash)
        blockchain.add_entry("CS-NAG-001", "AI_ANALYZED", "AI_ORCHESTRATOR", p_hash)
        blockchain.add_entry("CS-NAG-001", "ASSIGNED", "AUTHORITY_COMMAND_CENTER")
        blockchain.add_entry("CS-NAG-001", "ACCEPTED", "Vidarbha Infra Repairs")
        blockchain.add_entry("CS-NAG-001", "WORK_STARTED", "Vidarbha Infra Repairs")
        blockchain.add_entry("CS-NAG-001", "COMPLETION_UPLOADED", "Vidarbha Infra Repairs", p_hash)
        blockchain.add_entry("CS-NAG-001", "DRONE_VERIFIED", "DRONE_VERIFIER")
        blockchain.add_entry("CS-NAG-001", "CLOSED", "SYSTEM_CLOSE")
        
        blockchain.add_entry("CS-PUN-001", "COMPLAINT_SUBMITTED", "Priya Sharma", p_hash)
        blockchain.add_entry("CS-PUN-001", "AI_ANALYZED", "AI_ORCHESTRATOR", p_hash)
        blockchain.add_entry("CS-PUN-001", "ASSIGNED", "AUTHORITY_COMMAND_CENTER")
        blockchain.add_entry("CS-PUN-001", "ACCEPTED", "Pune City Utilities")
        
        blockchain.add_entry("CS-BLR-001", "COMPLAINT_SUBMITTED", "Siddharth Rao", p_hash)
        blockchain.add_entry("CS-BLR-001", "AI_ANALYZED", "AI_ORCHESTRATOR", p_hash)
        blockchain.add_entry("CS-BLR-001", "ASSIGNED", "AUTHORITY_COMMAND_CENTER")
        blockchain.add_entry("CS-BLR-001", "MANAGEMENT_COMPLAINT_FILED", "DRONE_AUTONOMOUS_SYSTEM")
        
        blockchain.add_entry("CS-DEL-001", "COMPLAINT_SUBMITTED", "Ananya Sen", p_hash)
        blockchain.add_entry("CS-DEL-001", "AI_ANALYZED", "AI_ORCHESTRATOR", p_hash)
        blockchain.add_entry("CS-DEL-001", "ASSIGNED", "AUTHORITY_COMMAND_CENTER")
        blockchain.add_entry("CS-DEL-001", "MANAGEMENT_COMPLAINT_FILED", "DRONE_AUTONOMOUS_SYSTEM")
        
        print("✅ Seeded: 20 hash-linked Blockchain entries successfully!")

    print("🎉 Database seeding sweep finished successfully.")

if __name__ == "__main__":
    seed_db()
