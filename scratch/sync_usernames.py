import os
import sys
import json

# Add project root to python path
sys.path.insert(0, r'c:\Users\User\Documents\RemindMe')

from backend.supabase_auth import supabase_admin
from backend_api.app.services.session_store import DATA_DIR

local_path = os.path.join(str(DATA_DIR), "usernames.json")

if not os.path.exists(local_path):
    print(f"Local usernames mapping file not found at {local_path}")
    sys.exit(1)

with open(local_path, "r", encoding="utf-8") as f:
    mappings = json.load(f)

print(f"Found {len(mappings)} local mappings. Syncing to Supabase...")

success_count = 0
failed_count = 0

for username, data in mappings.items():
    clean_username = username.strip().lower()
    email = data.get("email")
    uid = data.get("uid")
    avatar = data.get("avatar_emoji")
    metadata = data.get("metadata", {})
    
    payload = {
        "username": clean_username,
        "email": email,
        "uid": uid,
        "avatar_emoji": avatar,
        "metadata": metadata
    }
    
    try:
        res = supabase_admin.table("usernames").upsert(payload, on_conflict="username").execute()
        print(f"Synced: {clean_username} -> {email}")
        success_count += 1
    except Exception as e:
        print(f"FAILED to sync '{clean_username}': {e}")
        failed_count += 1

print("\n=== SYNC SUMMARY ===")
print(f"Successfully synced: {success_count}")
print(f"Failed:              {failed_count}")
