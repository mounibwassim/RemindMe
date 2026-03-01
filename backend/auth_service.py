import requests
from backend.config import FIREBASE_WEB_API_KEY
PROJECT_ID = "remindme-mounib"
FIRESTORE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"

def get_username_data(username):
    url = f"{FIRESTORE_URL}:runQuery?key={FIREBASE_WEB_API_KEY}"
    username_lower = username.strip().lower()
    payload = {
        "structuredQuery": {
            "from": [{"collectionId": "users"}],
            "where": {
                "fieldFilter": {
                    "field": {"fieldPath": "username"},
                    "op": "EQUAL",
                    "value": {"stringValue": username_lower}
                }
            }
        }
    }
    try:
        print(f"Firestore Query URL: {url}")
        r = requests.post(url, json=payload)
        data = r.json()
        print(f"Firestore Response Status: {r.status_code}")
        
        # Firestore runQuery returns a list of dictionaries. 
        # Missing docs just return {"readTime": ...}
        if isinstance(data, list) and len(data) > 0:
            doc = data[0].get("document")
            if doc and "fields" in doc:
                import json
                # Convert Firestore format: {"email": {"stringValue": "x"}}
                result = {k: list(v.values())[0] for k, v in doc["fields"].items()}
                if "metadata" in result and isinstance(result["metadata"], str):
                    try:
                        result["metadata"] = json.loads(result["metadata"])
                    except:
                        pass
                
                # Map document id back as uid
                doc_name = doc.get("name", "")
                result["uid"] = doc_name.split("/")[-1] if doc_name else ""
                return result, None

        return None, "USER_NOT_FOUND"
    except Exception as e:
        return None, str(e)

def save_username_mapping(username, email, uid, metadata=None):
    if not uid:
        return False, "Missing UID for cloud mapping"
        
    url = f"{FIRESTORE_URL}/users/{uid}?key={FIREBASE_WEB_API_KEY}"
    
    fields = {
        "username": {"stringValue": username},
        "email": {"stringValue": email}
    }
    
    if metadata:
        import json
        fields["metadata"] = {"stringValue": json.dumps(metadata)}
        
    payload = {"fields": fields}
    
    try:
        print(f"Firestore Sync: Patching {url}")
        r = requests.patch(url, json=payload)
        data = r.json()
        if r.status_code not in [200, 201]:
            err_msg = data.get("error", {}).get("message", "Unknown Firestore Error")
            print(f"Firestore Sync Error ({r.status_code}): {err_msg}")
            return False, err_msg
            
        print(f"Firestore Sync Success for UID: {uid}")
        return True, None
    except Exception as e:
        print(f"Firestore Sync Exception: {str(e)}")
        return False, str(e)

def write_audit_cloud(user_uid, action, task_title="", extra=""):
    """
    Log audit events to Firestore 'audit_logs' collection.
    """
    if not user_uid:
        print("Cloud Audit Error: Missing user_uid")
        return False, "Missing user_uid"
        
    print(f"DEBUG: writing audit for UID: {user_uid}, Action: {action}")
    url = f"{FIRESTORE_URL}/audit_logs?key={FIREBASE_WEB_API_KEY}"
    
    # Use ISO format for timestamp as native Firestore SERVER_TIMESTAMP 
    # via REST API requires specific format or transforms. 
    # ISO string is easier for cross-platform retrieval in Kivy.
    from datetime import datetime
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    fields = {
        "user_uid": {"stringValue": user_uid},
        "action": {"stringValue": action},
        "task_title": {"stringValue": task_title},
        "timestamp": {"stringValue": timestamp},
        "extra": {"stringValue": extra}
    }
    
    payload = {"fields": fields}
    
    try:
        r = requests.post(url, json=payload)
        if r.status_code not in [200, 201]:
            data = r.json()
            err = data.get("error", {}).get("message", "Unknown Error")
            print(f"Cloud Audit Error: {err}")
            return False, err
        return True, None
    except Exception as e:
        print(f"Cloud Audit Exception: {str(e)}")
        return False, str(e)
