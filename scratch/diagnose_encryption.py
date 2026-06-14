"""
Full encryption recovery diagnostic.
Checks Firebase for salts, queries Supabase for raw tasks,
and attempts decryption with found salts.
"""
import sys, os, json, base64
sys.path.insert(0, r'c:\Users\User\Documents\RemindMe')

import requests
from backend.config import FIREBASE_DATABASE_URL
from backend.crypto import derive_key, decrypt_bytes, load_salt_for
from backend_api.app.services.session_store import DATA_DIR

SEP = "=" * 60

print(SEP)
print("STEP 1: LOCAL SALT FILES")
print(SEP)
salt_dir = str(DATA_DIR)
if os.path.exists(salt_dir):
    salt_files = [f for f in os.listdir(salt_dir) if f.startswith("key_salt_")]
    if salt_files:
        for sf in salt_files:
            username = sf.replace("key_salt_", "").replace(".bin", "")
            salt_bytes = load_salt_for(username, path=salt_dir)
            print(f"  Found local salt for '{username}': {salt_bytes.hex() if salt_bytes else 'EMPTY'}")
    else:
        print("  NO local salt files found (Render filesystem was wiped)")
else:
    print(f"  DATA_DIR does not exist: {salt_dir}")

print()
print(SEP)
print("STEP 2: FIREBASE RTDB - Username Mappings & Cloud Salts")
print(SEP)
base_url = FIREBASE_DATABASE_URL.rstrip('/')
url = base_url + "/usernames.json"
try:
    r = requests.get(url, timeout=10)
    print(f"  Firebase RTDB status: {r.status_code}")
    fb_data = r.json()
    if fb_data and isinstance(fb_data, dict):
        cloud_salts = {}
        for username, val in fb_data.items():
            meta = val.get('metadata', {})
            salt_hex = meta.get('salt_hex') if isinstance(meta, dict) else None
            print(f"\n  User: '{username}'")
            print(f"    email : {val.get('email')}")
            print(f"    uid   : {val.get('uid')}")
            print(f"    salt_hex in cloud: {'YES -> ' + salt_hex[:16] + '...' if salt_hex else 'NO (missing!)'}")
            if salt_hex:
                cloud_salts[username] = {
                    "salt_hex": salt_hex,
                    "email": val.get("email"),
                    "uid": val.get("uid"),
                }
    else:
        print(f"  No data: {fb_data}")
        cloud_salts = {}
except Exception as e:
    print(f"  ERROR querying Firebase: {e}")
    cloud_salts = {}

print()
print(SEP)
print("STEP 3: LOCAL USERNAME MAPPING (usernames.json)")
print(SEP)
local_map_path = os.path.join(salt_dir, "usernames.json")
local_mappings = {}
if os.path.exists(local_map_path):
    with open(local_map_path, "r") as f:
        local_mappings = json.load(f)
    for uname, data in local_mappings.items():
        meta = data.get("metadata", {})
        salt_hex = meta.get("salt_hex") if isinstance(meta, dict) else None
        print(f"  User: '{uname}', email: {data.get('email')}, salt_hex in local map: {'YES' if salt_hex else 'NO'}")
        if salt_hex and uname not in cloud_salts:
            cloud_salts[uname] = {
                "salt_hex": salt_hex,
                "email": data.get("email"),
                "uid": data.get("uid"),
            }
else:
    print(f"  usernames.json NOT found at {local_map_path}")

print()
print(SEP)
print("STEP 4: SUPABASE - Raw Task Records")
print(SEP)
try:
    from backend.supabase_service import supabase as sb_client
    all_tasks = sb_client.table("tasks").select("*").order("created_at").execute()
    rows = all_tasks.data if all_tasks else []
    print(f"  Total tasks in database: {len(rows)}")
    
    # Group by user_id
    by_user = {}
    for row in rows:
        uid = row.get("user_id", "unknown")
        by_user.setdefault(uid, []).append(row)
    
    for uid, tasks in by_user.items():
        print(f"\n  User UID: {uid} — {len(tasks)} task(s)")
        for t in tasks[:3]:  # Show up to 3 tasks per user
            enc = t.get("encrypted_data", "")
            has_colon = ":" in enc if enc else False
            print(f"    Task ID: {t.get('id')}")
            print(f"    title field: '{t.get('title', '')}'")
            print(f"    encrypted_data present: {bool(enc)}, valid format: {has_colon}")
            if enc and has_colon:
                nonce_b64, ct_b64 = enc.split(":", 1)
                print(f"    nonce (b64, 16 chars): {nonce_b64[:16]}...")
                print(f"    ct_b64 (first 20 chars): {ct_b64[:20]}...")
except Exception as e:
    print(f"  ERROR querying Supabase: {e}")
    rows = []
    by_user = {}

print()
print(SEP)
print("STEP 5: DECRYPTION ATTEMPT")
print(SEP)

if not cloud_salts:
    print("  FATAL: No salts found anywhere (Firebase or local). Cannot attempt decryption.")
    print("  Conclusion: Cryptographic material is MISSING. Old task data cannot be recovered.")
else:
    print(f"  Found salts for: {list(cloud_salts.keys())}")
    # Map UID -> username for lookup
    uid_to_info = {}
    for uname, info in cloud_salts.items():
        uid = info.get("uid")
        if uid:
            uid_to_info[uid] = {"username": uname, **info}
    
    recovered = 0
    failed = 0
    for uid, tasks in by_user.items():
        info = uid_to_info.get(uid)
        if not info:
            print(f"\n  UID {uid}: No salt mapping found — CANNOT DECRYPT")
            failed += len(tasks)
            continue
        
        uname = info["username"]
        email = info["email"]
        salt_hex = info["salt_hex"]
        
        try:
            salt = bytes.fromhex(salt_hex)
        except Exception as e:
            print(f"\n  UID {uid} ({uname}): Invalid salt_hex — {e}")
            failed += len(tasks)
            continue
        
        # Derive key using same formula as session_store.py
        # key = derive_key(f"{username}:{email}:{uid}", salt)
        key = derive_key(f"{uname}:{email}:{uid}", salt)
        print(f"\n  Testing decryption for user '{uname}' (UID: {uid})")
        print(f"  Passphrase: '{uname}:{email}:{uid}'")
        
        for t in tasks:
            enc = t.get("encrypted_data", "")
            task_id = t.get("id")
            stored_title = t.get("title", "")
            if enc and ":" in enc:
                try:
                    nonce_b64, ct_b64 = enc.split(":", 1)
                    plaintext = decrypt_bytes(ct_b64, nonce_b64, key).decode("utf-8")
                    title = plaintext.split("\n", 1)[0]
                    print(f"    ✅ Task {task_id}: DECRYPTED -> '{title}'")
                    recovered += 1
                except Exception as e:
                    print(f"    ❌ Task {task_id}: FAILED ({e}) — stored title='{stored_title}'")
                    failed += 1
            else:
                print(f"    ⚠️  Task {task_id}: No encrypted_data — using stored title='{stored_title}'")

print()
print(SEP)
print("FINAL REPORT")
print(SEP)
print(f"  Tasks recoverable with current salt: {recovered if 'recovered' in dir() else 'N/A'}")
print(f"  Tasks failed decryption: {failed if 'failed' in dir() else 'N/A'}")
print(f"  Cloud salts found: {len(cloud_salts)}")
