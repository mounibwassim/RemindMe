import requests
import json
import os

from backend.config import FIREBASE_WEB_API_KEY

def get_api_key():
    if "YOUR_FIREBASE" in FIREBASE_WEB_API_KEY:
        # Check env var as backup
        return os.environ.get("FIREBASE_API_KEY")
    return FIREBASE_WEB_API_KEY

def reset_password_email(email):
    """
    Send password reset email using Firebase REST API.
    """
    key = get_api_key()
    if not key:
        return None, "Missing Firebase API Key"
        
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={key}"
    payload = {
        "requestType": "PASSWORD_RESET",
        "email": email
    }
    
    try:
        # Explicitly set locale to English to help with deliverability/formatting
        headers = {"X-Firebase-Locale": "en"}
        r = requests.post(url, json=payload, headers=headers)
        data = r.json()
        if "error" in data:
            return None, data["error"]["message"]
        # Success: returns email
        return data, None
    except Exception as e:
        return None, str(e)

def sign_in_with_email_password(email, password):
    """
    Sign in using Firebase REST API.
    Returns: (dict response_data, str error_message)
    """
    key = get_api_key()
    if not key:
        return None, "Missing Firebase API Key"
        
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={key}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    
    try:
        r = requests.post(url, json=payload)
        data = r.json()
        if "error" in data:
            return None, data["error"]["message"]
        return data, None
    except Exception as e:
        return None, str(e)

def sign_up_with_email_password(email, password):
    """
    Sign up new user using Firebase REST API.
    """
    key = get_api_key()
    if not key:
        return None, "Missing Firebase API Key"
        
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={key}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    
    try:
        r = requests.post(url, json=payload)
        data = r.json()
        if "error" in data:
            return None, data["error"]["message"]
        return data, None
    except Exception as e:
        return None, str(e)

def get_user_data(id_token):
    """
    Get user profile data using ID Token.
    """
    key = get_api_key()
    if not key:
        return None
        
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={key}"
    payload = {"idToken": id_token}
    
    try:
        r = requests.post(url, json=payload)
        data = r.json()
        if "users" in data:
            return data["users"][0]
        return None
    except:
        return None

def update_password(id_token, new_password):
    """
    Update logged-in user's password.
    """
    key = get_api_key()
    if not key:
        return None, "Missing Config"
        
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={key}"
    payload = {
        "idToken": id_token,
        "password": new_password,
        "returnSecureToken": True
    }
    
    try:
        r = requests.post(url, json=payload)
        data = r.json()
        if "error" in data:
            return None, data["error"]["message"]
        return data, None
    except Exception as e:
        return None, str(e)
from backend.config import FIREBASE_WEB_API_KEY, FIREBASE_DATABASE_URL

def save_username_mapping(username, email, uid, metadata=None):
    """
    Save username to email mapping and optional encryption metadata in Realtime DB.
    """
    url = f"{FIREBASE_DATABASE_URL}usernames/{username}.json"
    payload = {"email": email, "uid": uid}
    if metadata:
        payload["metadata"] = metadata
    try:
        r = requests.put(url, json=payload)
        return r.status_code == 200, None
    except Exception as e:
        return False, str(e)

def get_username_data(username):
    """
    Fetch all data for a given username from cloud.
    Reads from Firestore (primary store) with RTDB as fallback.
    """
    username_lower = username.strip().lower()
    
    # --- 1. Try Firestore first (primary store) ---
    try:
        fs_url = f"https://firestore.googleapis.com/v1/projects/remindme-mounib/databases/(default)/documents:runQuery?key={FIREBASE_WEB_API_KEY}"
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
        r = requests.post(fs_url, json=payload)
        print(f"Firestore login lookup: status={r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and len(data) > 0:
                doc = data[0].get("document")
                if doc and "fields" in doc:
                    fields = doc["fields"]
                    result = {k: list(v.values())[0] for k, v in fields.items()}
                    if "metadata" in result and isinstance(result["metadata"], str):
                        try:
                            result["metadata"] = json.loads(result["metadata"])
                        except:
                            pass
                    doc_name = doc.get("name", "")
                    result["uid"] = doc_name.split("/")[-1] if doc_name else ""
                    print(f"Firestore: found user {username_lower}")
                    return result, None
        print("Firestore: user not found, falling back to RTDB")
    except Exception as e:
        print(f"Firestore lookup failed: {e}")

    # --- 2. RTDB fallback ---
    try:
        url = f"{FIREBASE_DATABASE_URL}usernames/{username_lower}.json"
        r = requests.get(url)
        data = r.json()
        if data and not isinstance(data, str):
            print(f"RTDB: found user {username_lower}")
            return data, None
        # Try exact case as fallback
        url2 = f"{FIREBASE_DATABASE_URL}usernames/{username}.json"
        r2 = requests.get(url2)
        data2 = r2.json()
        if data2 and not isinstance(data2, str):
            print(f"RTDB (original case): found user {username}")
            return data2, None
        return None, "Username not found in cloud."
    except Exception as e:
        return None, str(e)

def update_profile(id_token, display_name):
    """
    Update user's display name (Username).
    """
    key = get_api_key()
    if not key:
        return None, "Missing Config"
        
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={key}"
    payload = {
        "idToken": id_token,
        "displayName": display_name,
        "returnSecureToken": True
    }
    
    try:
        r = requests.post(url, json=payload)
        data = r.json()
        if "error" in data:
            return None, data["error"]["message"]
        return data, None
    except Exception as e:
        return None, str(e)
