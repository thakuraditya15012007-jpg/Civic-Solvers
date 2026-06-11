"""
pubsub_workers.py — Decoupled event-driven backend tasks pipeline.
Supports real Google Cloud Pub/Sub client and asynchronous local background thread execution
when GCP environment variables are absent. Satisfies: Rule 9 (Decoupled Event Architecture).
"""
import json
import time
import threading
import uuid
from config import GCP_PROJECT_ID

# ── Pub/Sub Client Initialization ───────────────────────────────────────────

pubsub_available = False
publisher_client = None

try:
    from google.cloud import pubsub_v1
    publisher_client = pubsub_v1.PublisherClient()
    pubsub_available = True
    print("✅ Pub/Sub Publisher Client initialized.")
except Exception as e:
    print(f"⚠️ Pub/Sub Client initialization failed: {e}. Event architecture will run via Local Background Thread.")

# ── Local Background Worker Execution ───────────────────────────────────────

def _local_worker_daemon(payload: dict) -> None:
    """Executes long-running AI pipelines or drone scans in a background thread."""
    try:
        # Delay briefly to let Streamlit update the web UI first
        time.sleep(1.5)
        event_type = payload.get("event_type")
        print(f"⚙️ [Local Background Worker] Processing event: {event_type}...")

        if event_type == "NEW_COMPLAINT":
            from backend import ai_engine
            from backend.gcp_manager import download_gcs_bytes
            from backend.gcp_manager import update_complaint_status
            
            complaint_id = payload.get("complaint_id")
            metadata = payload.get("metadata", {})
            
            # Transition status to AI_ANALYZING first
            update_complaint_status(
                complaint_id, "AI_ANALYZING", 
                "Autonomous Vision, Risk, and Memory evaluation triggered.", "AI_ORCHESTRATOR"
            )
            
            photo_path = metadata.get("photo_path")
            image_bytes = download_gcs_bytes(photo_path)
            
            # Run the multi-agent pipeline
            ai_engine.run_full_ai_pipeline(complaint_id, image_bytes, metadata)

        elif event_type == "COMPLETION_UPLOADED":
            from backend import drone_verifier
            from backend.gcp_manager import update_complaint_status
            
            complaint_id = payload.get("complaint_id")
            before_uri = payload.get("before_photo_path")
            after_uri = payload.get("after_photo_path")
            
            # Transition status to DRONE_SCANNING first
            update_complaint_status(
                complaint_id, "DRONE_SCANNING", 
                "Autonomous Drone dispatched to scan repairs. Verification in progress.", "DRONE_VERIFIER"
            )
            
            time.sleep(1.5)
            # Run verifier comparison
            drone_verifier.verify_repair(complaint_id, before_uri, after_uri)

        elif event_type == "DRONE_PATROL":
            from backend import drone_verifier
            drone_verifier.drone_patrol_and_escalate()

        elif event_type == "AWARD_POINTS":
            from backend import gamification
            gamification.award_points(
                payload.get("aadhar_hash"),
                payload.get("rule_key"),
                payload.get("reason"),
                payload.get("complaint_id")
            )
        
        print(f"✅ [Local Background Worker] Event {event_type} processed successfully.")
    except Exception as e:
        print(f"❌ [Local Background Worker] Critical failure during background processing: {e}")

# ── Universal Interface ──────────────────────────────────────────────────────

def publish_event(topic_id: str, payload: dict) -> str:
    """
    Publish an event to Pub/Sub.
    If cloud Pub/Sub is unavailable, falls back to a background thread to prevent blocking the UI.
    """
    payload_json = json.dumps(payload).encode("utf-8")
    
    if pubsub_available:
        try:
            topic_path = publisher_client.topic_path(GCP_PROJECT_ID, topic_id)
            future = publisher_client.publish(topic_path, payload_json)
            msg_id = future.result()
            print(f"📡 [GCP Pub/Sub] Published event {payload.get('event_type')} to {topic_id} | Msg ID: {msg_id}")
            return msg_id
        except Exception as e:
            print(f"⚠️ [GCP Pub/Sub] Publish failed: {e}. Defaulting to Local Background Worker.")
            # Fall through to local thread fallback
    
    # Asynchronous Local Background Thread Fallback (Rule 9: Non-blocking)
    msg_id = f"mock-msg-{str(uuid.uuid4())[:8]}"
    print(f"📡 [Local Mock Pub/Sub] Queueing event {payload.get('event_type')} | Mock Msg ID: {msg_id}")
    
    thread = threading.Thread(target=_local_worker_daemon, args=(payload,))
    thread.daemon = True
    thread.start()
    
    return msg_id

def process_civic_event(message) -> None:
    """
    Subscriber callback for cloud execution environment.
    All exceptions caught to satisfy Rule 2/Persistent skill error boundary.
    """
    try:
        data_str = message.data.decode("utf-8")
        payload = json.loads(data_str)
        event_type = payload.get("event_type")
        
        print(f"📥 [PubSub Subscriber] Dequeued event: {event_type}")
        
        if event_type == "NEW_COMPLAINT":
            from backend import ai_engine
            from backend.gcp_manager import download_gcs_bytes
            complaint_id = payload.get("complaint_id")
            metadata = payload.get("metadata", {})
            photo_path = metadata.get("photo_path")
            image_bytes = download_gcs_bytes(photo_path)
            ai_engine.run_full_ai_pipeline(complaint_id, image_bytes, metadata)
            
        elif event_type == "COMPLETION_UPLOADED":
            from backend import drone_verifier
            complaint_id = payload.get("complaint_id")
            before_uri = payload.get("before_photo_path")
            after_uri = payload.get("after_photo_path")
            drone_verifier.verify_repair(complaint_id, before_uri, after_uri)
            
        elif event_type == "DRONE_PATROL":
            from backend import drone_verifier
            drone_verifier.drone_patrol_and_escalate()
            
        elif event_type == "AWARD_POINTS":
            from backend import gamification
            gamification.award_points(
                payload.get("aadhar_hash"),
                payload.get("rule_key"),
                payload.get("reason"),
                payload.get("complaint_id")
            )
            
        message.ack()
    except Exception as e:
        print(f"❌ [PubSub Subscriber] Error processing message: {e}")
        # In cloud environments, we may nack or simply log depending on policy
        if hasattr(message, "nack"):
            message.nack()
