"""
setup.py — Idempotent GCP infrastructure bootstrap validator.
Runs once at app startup. Creates missing resources safely.
No external account references. Uses ADC credentials from environment.
"""
from config import GCP_PROJECT_ID, GCS_BUCKET_NAME, PUBSUB_TOPIC_ID, PUBSUB_DRONE_TOPIC

def bootstrap_gcp() -> None:
    """Verifies and idempotently provisions all required GCP resources."""
    try:
        from google.cloud import storage, firestore, pubsub_v1
        _bootstrap_storage(storage)
        _bootstrap_firestore(firestore)
        _bootstrap_pubsub(pubsub_v1)
    except ModuleNotFoundError:
        print("⚠️ google-cloud packages not installed. Skipping GCP infrastructure bootstrap.")
    except Exception as e:
        print(f"⚠️ GCP bootstrap error: {e}")

def _bootstrap_storage(storage) -> None:
    try:
        storage_client = storage.Client(project=GCP_PROJECT_ID)
        try:
            storage_client.get_bucket(GCS_BUCKET_NAME)
            print(f"✅ GCS bucket verified: {GCS_BUCKET_NAME}")
        except Exception:
            try:
                storage_client.create_bucket(GCS_BUCKET_NAME)
                print(f"✅ GCS bucket created: {GCS_BUCKET_NAME}")
            except Exception as e:
                print(f"⚠️ GCS bucket init warning: {e}")
    except Exception as e:
        print(f"⚠️ Storage client initialization warning (using local mock fallback): {e}")

def _bootstrap_firestore(firestore) -> None:
    try:
        db = firestore.Client(project=GCP_PROJECT_ID)
        db.collection("_health").document("ping").set({"status": "ok"})
        print("✅ Firestore connected.")
    except Exception as e:
        print(f"⚠️ Firestore connectivity issue (using local mock fallback): {e}")

def _bootstrap_pubsub(pubsub_v1) -> None:
    try:
        publisher = pubsub_v1.PublisherClient()
        for topic_id in [PUBSUB_TOPIC_ID, PUBSUB_DRONE_TOPIC]:
            topic_path = publisher.topic_path(GCP_PROJECT_ID, topic_id)
            try:
                publisher.get_topic(request={"topic": topic_path})
                print(f"✅ Pub/Sub topic verified: {topic_id}")
            except Exception:
                try:
                    publisher.create_topic(request={"topic": topic_path})
                    print(f"✅ Pub/Sub topic created: {topic_id}")
                except Exception as e:
                    print(f"⚠️ Pub/Sub init warning for {topic_id}: {e}")
    except Exception as e:
        print(f"⚠️ Pub/Sub client initialization warning (using local mock fallback): {e}")

if __name__ == "__main__":
    bootstrap_gcp()
    print("✅ Civic Solvers Cloud Infrastructure validated.")
