"""
Phase 2: Attempt decryption using LOCAL salts against Supabase tasks.
The Supabase user_id (UUID) does not always match the Firebase uid stored in mappings.
We brute-force match by trying all salts against all tasks.
"""
import sys, os, json
sys.path.insert(0, r'c:\Users\User\Documents\RemindMe')

from backend.crypto import derive_key, decrypt_bytes, load_salt_for
from backend_api.app.services.session_store import DATA_DIR
from backend.supabase_auth import save_username_mapping, get_username_data

SEP = "=" * 60

# ── Load all local salts ──────────────────────────────────
salt_dir = str(DATA_DIR)
local_salts = {}
for fname in os.listdir(salt_dir):
    if fname.startswith("key_salt_") and fname.endswith(".bin"):
        uname = fname.replace("key_salt_", "").replace(".bin", "")
        salt = load_salt_for(uname, path=salt_dir)
        if salt:
            local_salts[uname] = salt
            
print(f"Local salts found: {list(local_salts.keys())}")

# ── Load Firebase username→email+uid mapping ──────────────
local_map_path = os.path.join(salt_dir, "usernames.json")
with open(local_map_path, "r") as f:
    username_map = json.load(f)

# Build candidate (username, email, uid) combos
candidates = []
for uname, salt in local_salts.items():
    info = username_map.get(uname, {})
    email = info.get("email", "")
    uid = info.get("uid", "")
    candidates.append({
        "username": uname,
        "email": email,
        "uid": uid,
        "salt": salt,
    })
    print(f"  Candidate: username='{uname}', email='{email}', uid='{uid}'")

print()
print(SEP)
print("STEP: Fetch all tasks from Supabase")
print(SEP)

from backend.supabase_service import supabase as sb
all_tasks_resp = sb.table("tasks").select("*").execute()
rows = all_tasks_resp.data if all_tasks_resp else []
print(f"Total tasks: {len(rows)}")

# Group by user_id
by_uid = {}
for row in rows:
    uid = row.get("user_id", "?")
    by_uid.setdefault(uid, []).append(row)

print(f"Distinct user_ids in Supabase: {list(by_uid.keys())}")
print()
print(SEP)
print("STEP: Brute-force salt matching")
print(SEP)

recovery_map = {}  # supabase_uid -> (username, key)

for supabase_uid, tasks in by_uid.items():
    print(f"\nTesting Supabase UID: {supabase_uid} ({len(tasks)} tasks)")
    
    # Try each candidate
    for cand in candidates:
        uname = cand["username"]
        email = cand["email"]
        firebase_uid = cand["uid"]
        salt = cand["salt"]
        
        # Try passphrase with firebase uid (original stored uid)
        for uid_to_use in [firebase_uid, supabase_uid]:
            passphrase = f"{uname}:{email}:{uid_to_use}"
            key = derive_key(passphrase, salt)
            
            # Test against first encrypted task
            test_task = next((t for t in tasks if t.get("encrypted_data") and ":" in t.get("encrypted_data", "")), None)
            if not test_task:
                continue
                
            enc = test_task.get("encrypted_data", "")
            try:
                nonce_b64, ct_b64 = enc.split(":", 1)
                plaintext = decrypt_bytes(ct_b64, nonce_b64, key).decode("utf-8")
                title = plaintext.split("\n", 1)[0]
                print(f"  [MATCH] username='{uname}', uid_used='{uid_to_use[:20]}...', decrypted='{title}'")
                recovery_map[supabase_uid] = {
                    "username": uname,
                    "email": email,
                    "passphrase_uid": uid_to_use,
                    "key": key,
                    "salt": salt,
                }
                break
            except Exception:
                pass
        
        if supabase_uid in recovery_map:
            break
    
    if supabase_uid not in recovery_map:
        print(f"  [FAIL] NO MATCH for UID {supabase_uid} -- all {len(candidates)} salt candidates failed")

print()
print(SEP)
print("FULL DECRYPTION OF ALL TASKS")
print(SEP)

total_recovered = 0
total_failed = 0
decrypted_tasks = []  # For potential re-encryption

for supabase_uid, tasks in by_uid.items():
    info = recovery_map.get(supabase_uid)
    if not info:
        print(f"\n[UID {supabase_uid}] — NO KEY FOUND, all {len(tasks)} tasks unrecoverable")
        total_failed += len(tasks)
        continue
    
    key = info["key"]
    uname = info["username"]
    print(f"\n[UID {supabase_uid}] — user '{uname}':")
    
    for t in tasks:
        enc = t.get("encrypted_data", "")
        task_id = t.get("id")
        stored_title = t.get("title", "")
        if enc and ":" in enc:
            try:
                nonce_b64, ct_b64 = enc.split(":", 1)
                plaintext = decrypt_bytes(ct_b64, nonce_b64, key).decode("utf-8")
                parts = plaintext.split("\n", 1)
                title = parts[0]
                desc = parts[1] if len(parts) > 1 else ""
                print(f"  [OK] '{stored_title}' -> decrypted='{title}'")
                total_recovered += 1
                decrypted_tasks.append({
                    "task_id": task_id,
                    "supabase_uid": supabase_uid,
                    "username": uname,
                    "decrypted_title": title,
                    "decrypted_desc": desc,
                    "stored_title": stored_title,
                })
            except Exception as e:
                print(f"  [FAIL] Task {task_id} (stored: '{stored_title}') FAILED: {e}")
                total_failed += 1
        else:
            print(f"  [WARN] Task {task_id}: no encrypted_data, raw title='{stored_title}'")
            total_recovered += 1

print()
print(SEP)
print("REPORT")
print(SEP)
print(f"Tasks successfully decrypted: {total_recovered}")
print(f"Tasks failed:                 {total_failed}")
print(f"Users with matching keys:     {len(recovery_map)}")
print(f"Users without keys:           {len(by_uid) - len(recovery_map)}")

# Save recovery map for use in fix script
recovery_save = {}
for uid, info in recovery_map.items():
    recovery_save[uid] = {
        "username": info["username"],
        "email": info["email"],
        "passphrase_uid": info["passphrase_uid"],
        "salt_hex": info["salt"].hex(),
    }
out_path = os.path.join(salt_dir, "recovery_map.json")
with open(out_path, "w") as f:
    json.dump(recovery_save, f, indent=2)
print(f"\nRecovery map saved to: {out_path}")
