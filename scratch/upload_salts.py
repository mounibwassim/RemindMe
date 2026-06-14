"""
Phase 3: Upload correct salts to Firebase cloud mapping.
This makes Render able to restore salts on login.
"""
import sys, os, json
sys.path.insert(0, r'c:\Users\User\Documents\RemindMe')

from backend.crypto import load_salt_for
from backend_api.app.services.session_store import DATA_DIR
from backend.supabase_auth import get_username_data, save_username_mapping

salt_dir = str(DATA_DIR)

# Load recovery map (which tells us which passphrase works per supabase UID)
recovery_map_path = os.path.join(salt_dir, "recovery_map.json")
with open(recovery_map_path, "r") as f:
    recovery_map = json.load(f)

print("=== UPLOADING SALTS TO FIREBASE CLOUD ===")
print()

for supabase_uid, info in recovery_map.items():
    username = info["username"]
    email = info["email"]
    salt_hex = info["salt_hex"]
    # The actual passphrase uid that works for decryption
    passphrase_uid = info["passphrase_uid"]
    
    print(f"User: '{username}' (Supabase UID: {supabase_uid})")
    print(f"  Salt hex: {salt_hex[:16]}...")
    print(f"  Passphrase UID used: {passphrase_uid[:20]}...")
    
    # Get current Firebase data
    user_data, err = get_username_data(username)
    if err or not user_data:
        print(f"  [WARN] Could not find Firebase mapping for '{username}': {err}")
        # Still save it
        uid_for_firebase = user_data.get("uid") if user_data else passphrase_uid
    else:
        uid_for_firebase = user_data.get("uid", passphrase_uid)
    
    # Save to Firebase with the salt AND the correct supabase_uid for key derivation
    metadata = {
        "salt_hex": salt_hex,
        "supabase_uid": supabase_uid,  # NEW: store Supabase UUID separately
        "passphrase_uid": passphrase_uid,  # The exact uid used in PBKDF2
    }
    ok, err2 = save_username_mapping(username, email, uid_for_firebase, metadata=metadata)
    print(f"  Firebase upload: {'OK' if ok else 'FAILED - ' + str(err2)}")
    print()

print("=== DONE ===")
print("Now the backend (Render) can restore salts from Firebase on login.")
