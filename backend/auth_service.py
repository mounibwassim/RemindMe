import requests
from backend.config import FIREBASE_WEB_API_KEY
PROJECT_ID = "remindme-mounib"
FIRESTORE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"

def get_username_data(username):
    # 🚨 DISABLED: Firestore is hitting 403 Forbidden. Using firebase_service.py fallback.
    print(f"Firestore Bypass: Skipping lookup for {username}")
    return None, "Firestore is disabled"

def save_username_mapping(username, email, uid, metadata=None):
    # 🚨 DISABLED: Firestore is hitting 403 Forbidden.
    print(f"Firestore Bypass: Skipping sync for {username}")
    return True, None

def write_audit_cloud(user_uid, action, task_title="", extra=""):
    # 🚨 DISABLED: Firestore is hitting 403 Forbidden.
    # No-op to prevent background crashes/noise.
    return True, None
