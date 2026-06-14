"""
Full end-to-end backend test.
Run from project root:
  .\\backend_api\\.venv\\Scripts\\python.exe scratch/e2e_test.py
"""
import os, sys, json, requests, time

sys.path.insert(0, r'c:\Users\User\Documents\RemindMe')
from backend.supabase_auth import (
    supabase_admin,
    get_username_data, save_username_mapping,
    sign_in_with_email_password,
    get_auth_user_by_email,
    reset_password_email,
    confirm_password_reset,
)

BASE = "http://127.0.0.1:8000/api/v1"
SEP  = "=" * 60

def section(title):
    print(f"\n{SEP}\n{title}\n{SEP}")

# ── 1. Check Supabase connection ──────────────────────────────
section("1. Supabase: usernames table")
res = supabase_admin.table("usernames").select("username,email,uid,metadata").execute()
print(f"Total rows: {len(res.data)}")
for row in res.data:
    uid_display = row.get('uid','?')[:20]
    meta = row.get('metadata') or {}
    passphrase = (meta.get('passphrase_uid') or '')[:20]
    print(f"  {row['username']:<20}  uid={uid_display}  passphrase={passphrase}")

# ── 2. Fix mounib UID if it is legacy_mounib ─────────────────
section("2. Fix mounib uid if legacy")
mounib_row = supabase_admin.table("usernames").select("*").eq("username","mounib").execute()
if mounib_row.data:
    row = mounib_row.data[0]
    if row.get("uid") == "legacy_mounib":
        # Get real Supabase UID from metadata
        meta = row.get("metadata") or {}
        real_uid = meta.get("supabase_uid") or meta.get("passphrase_uid")
        if real_uid:
            supabase_admin.table("usernames").update({"uid": real_uid}).eq("username","mounib").execute()
            print(f"Fixed mounib uid: legacy_mounib -> {real_uid}")
        else:
            print("ERROR: No supabase_uid in mounib metadata!")
    else:
        print(f"mounib uid is already OK: {row.get('uid','?')[:20]}")
else:
    print("ERROR: mounib not found in usernames table!")

# ── 3. Test username lookup via backend ───────────────────────
section("3. Backend: username lookup mounib")
try:
    data, err = get_username_data("mounib")
    if err:
        print(f"FAIL: {err}")
    else:
        print(f"OK: email={data.get('email')}, uid={str(data.get('uid',''))[:20]}")
except Exception as e:
    print(f"EXCEPTION: {e}")

# ── 4. Test Supabase auth sign-in ─────────────────────────────
MOUNIB_EMAIL = "mounibwassimm@gmail.com"
MOUNIB_PASSWORD = "test123456"  # <-- will fail on wrong password; that's OK
section(f"4. Supabase sign-in for {MOUNIB_EMAIL}")
try:
    data, err = sign_in_with_email_password(MOUNIB_EMAIL, MOUNIB_PASSWORD)
    if err:
        print(f"Sign-in failed (expected if password wrong): {err}")
    else:
        print(f"Sign-in OK! UID={data.get('localId','?')[:20]}")
except Exception as e:
    print(f"EXCEPTION: {e}")

# ── 5. HTTP smoke test: /api/v1/auth/firebase/signin ─────────
section("5. HTTP POST /api/v1/auth/firebase/signin  (mounib)")
try:
    r = requests.post(f"{BASE}/auth/firebase/signin",
                      json={"username": "mounib", "password": MOUNIB_PASSWORD},
                      timeout=10)
    print(f"Status: {r.status_code}")
    body = r.json() if r.headers.get("content-type","").startswith("application/json") else r.text
    print(f"Body: {json.dumps(body, indent=2)[:500]}")
except Exception as e:
    print(f"HTTP request failed: {e}")

# ── 6. HTTP smoke test: forgot-password for mounib ──────────
section("6. HTTP POST /api/v1/auth/firebase/forgot-password (mounib)")
try:
    r = requests.post(f"{BASE}/auth/firebase/forgot-password",
                      json={"username": "mounib"},
                      timeout=15)
    print(f"Status: {r.status_code}")
    body = r.json() if r.headers.get("content-type","").startswith("application/json") else r.text
    print(f"Body: {json.dumps(body, indent=2)[:500]}")
except Exception as e:
    print(f"HTTP request failed: {e}")

# ── 7. HTTP smoke test: forgot-password for wassim ──────────
section("7. HTTP POST /api/v1/auth/firebase/forgot-password (wassim)")
try:
    r = requests.post(f"{BASE}/auth/firebase/forgot-password",
                      json={"username": "wassim"},
                      timeout=15)
    print(f"Status: {r.status_code}")
    body = r.json() if r.headers.get("content-type","").startswith("application/json") else r.text
    print(f"Body: {json.dumps(body, indent=2)[:500]}")
except Exception as e:
    print(f"HTTP request failed: {e}")

# ── 8. Final usernames table dump ────────────────────────────
section("8. Final usernames table dump")
res2 = supabase_admin.table("usernames").select("username,email,uid").execute()
print(json.dumps(res2.data, indent=2))

print(f"\n{SEP}\nDone.\n{SEP}")
