import requests
import json
import os

from backend.config import FIREBASE_WEB_API_KEY, FIREBASE_DATABASE_URL

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

def verify_password_reset_code(oob_code):
    key = get_api_key()
    if not key:
        return None, "Missing Firebase API Key"

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:resetPassword?key={key}"
    payload = {"oobCode": oob_code}

    try:
        r = requests.post(url, json=payload)
        data = r.json()
        if "error" in data:
            return None, data["error"]["message"]
        return data, None
    except Exception as e:
        return None, str(e)

def confirm_password_reset(oob_code, new_password):
    key = get_api_key()
    if not key:
        return None, "Missing Firebase API Key"

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:resetPassword?key={key}"
    payload = {
        "oobCode": oob_code,
        "newPassword": new_password,
    }

    try:
        r = requests.post(url, json=payload)
        data = r.json()
        if "error" in data:
            return None, data["error"]["message"]
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

def save_username_mapping(username, email, uid, metadata=None):
    """
    Save username to email mapping and optional encryption metadata in local fallback mirror and Realtime DB.
    """
    clean_username = username.strip().lower()
    payload = {"email": email, "uid": uid}
    if metadata:
        payload["metadata"] = metadata

    # 1. Save locally for guaranteed access and offline safety
    try:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend_api", "data")
        os.makedirs(data_dir, exist_ok=True)
        local_path = os.path.join(data_dir, "usernames.json")
        
        mappings = {}
        if os.path.exists(local_path):
            try:
                with open(local_path, "r", encoding="utf-8") as f:
                    mappings = json.load(f)
            except Exception:
                pass
        
        mappings[clean_username] = payload
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(mappings, f, indent=2)
    except Exception as e:
        print(f"Local username mirror save error: {e}")

    # 2. Save to cloud RTDB
    base_url = FIREBASE_DATABASE_URL.rstrip('/')
    url = f"{base_url}/usernames/{clean_username}.json"
    try:
        r = requests.put(url, json=payload, timeout=5)
        return r.status_code == 200, None
    except Exception as e:
        return False, str(e)

def get_username_data(username):
    """
    Fetch all data for a given username from local mirror or cloud RTDB fallback.
    """
    query_val = username.strip().lower()
    if "@" in query_val:
        return None, "Email lookup bypasses mapping lookup."

    # 1. Check local mapping mirror first (instant and foolproof)
    try:
        local_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend_api", "data", "usernames.json")
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as f:
                mappings = json.load(f)
            if query_val in mappings:
                print(f"Local mirror mapping found for {query_val}")
                return mappings[query_val], None
    except Exception as e:
        print(f"Local mirror mapping read error: {e}")

    # 2. RTDB fallback
    try:
        base_url = FIREBASE_DATABASE_URL.rstrip('/')
        url = f"{base_url}/usernames/{query_val}.json"
        
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
             print(f"RTDB: Database error or node not found (Status {r.status_code})")
             return None, "USER_NOT_FOUND"

        data = r.json()
        if data and isinstance(data, dict):
            if "error" in data:
                return None, "USER_NOT_FOUND"
            if "email" in data:
                print(f"RTDB: found user {query_val}")
                return data, None
            
        return None, "USER_NOT_FOUND"
    except Exception as e:
        return None, f"Cloud lookup failed: {str(e)}"

def get_username_by_email(email):
    """
    Reverse lookup: Find username mapped to a specific email.
    """
    query_email = email.strip().lower()
    
    # 1. Check local mapping mirror
    try:
        local_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend_api", "data", "usernames.json")
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as f:
                mappings = json.load(f)
            for uname, data in mappings.items():
                if data.get("email", "").strip().lower() == query_email:
                    return uname
    except Exception as e:
        print(f"Local mapping reverse lookup error: {e}")

    # 2. RTDB fallback - search for mapping
    try:
        base_url = FIREBASE_DATABASE_URL.rstrip('/')
        url = f"{base_url}/usernames.json"
        
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data and isinstance(data, dict):
                for uname, val in data.items():
                    if val.get("email", "").strip().lower() == query_email:
                        return uname
    except Exception as e:
        print(f"Cloud mapping reverse lookup error: {e}")
        
    return None

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


def update_avatar_in_mapping(username, emoji):
    """Update only the avatar_emoji in local and cloud mappings."""
    clean_username = username.strip().lower()
    
    # 1. Update local mapping mirror
    try:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend_api", "data")
        local_path = os.path.join(data_dir, "usernames.json")
        
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as f:
                mappings = json.load(f)
            
            if clean_username in mappings:
                mappings[clean_username]["avatar_emoji"] = emoji
                with open(local_path, "w", encoding="utf-8") as f:
                    json.dump(mappings, f, indent=2)
                    print(f"DEBUG: Local avatar updated for {clean_username}: {emoji}")
    except Exception as e:
        print(f"Local avatar update error: {e}")

    # 2. Update cloud RTDB
    base_url = FIREBASE_DATABASE_URL.rstrip('/')
    url = f"{base_url}/usernames/{clean_username}/avatar_emoji.json"
    try:
        r = requests.put(url, json=emoji, timeout=5)
        return r.status_code == 200, None
    except Exception as e:
        return False, str(e)
