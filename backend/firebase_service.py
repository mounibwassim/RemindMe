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
    base_url = FIREBASE_DATABASE_URL.rstrip('/')
    url = f"{base_url}/usernames/{username}.json"
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
    Fetch all data for a given username or email from cloud.
    Reads from Firestore (primary store) with RTDB as fallback.
    """
    query_val = username.strip().lower()
    is_email = "@" in query_val
    search_field = "email" if is_email else "username"
    
    # --- 1. Firestore Bypass (Disabled due to persistent 403 errors) ---
    """
    try:
        # Firestore is currently returning 403 Forbidden. Skipping to RTDB fallback.
        pass
    except Exception as e:
        print(f"Firestore lookup skipped: {e}")
    """

    # --- 2. RTDB fallback ---
    try:
        if is_email:
            # RTDB is indexed by username, searching by email in RTDB is slow/inefficient 
            # unless we have a mapping. For now, we try to use the username retrieval.
            # If the user entered an email, we can't easily find them in RTDB 'usernames/' 
            # node which is keyed by username. 
            print("RTDB: Email-based search in RTDB fallback is limited.")
            return None, "Firestore is restricted and email search is not indexed in RTDB fallback."
            
        # Ensure base URL has no trailing slash and path has leading slash
        base_url = FIREBASE_DATABASE_URL.rstrip('/')
        url = f"{base_url}/usernames/{query_val}.json"
        
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
             print(f"RTDB: Database error or node not found (Status {r.status_code})")
             return None, "USER_NOT_FOUND"

        data = r.json()
        if data and isinstance(data, dict):
            if "error" in data:
                print(f"RTDB: API Error: {data['error']}")
                return None, "USER_NOT_FOUND"
                
            if "email" in data:
                print(f"RTDB: found user {query_val}")
                return data, None
            else:
                print(f"RTDB: node {query_val} exists but is not a user (missing email).")
                return None, "Cloud data corrupted: missing email."
            
        return None, "USER_NOT_FOUND"
    except Exception as e:
        return None, f"Cloud lookup failed: {str(e)}"

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
