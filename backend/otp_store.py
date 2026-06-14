import sqlite3
import os
import time
import datetime
import hashlib
import secrets
import logging
import threading
import requests
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

logger = logging.getLogger("backend_api")

# Load environment
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend_api", ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

# Initialize isolated Supabase Client for OTP store to prevent circular dependencies
supabase_admin: Client = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    try:
        supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    except Exception as e:
        logger.error("[Forgot Password] [OTP Store] Failed to initialize Supabase client: %s", e)

# Thread-safe in-memory store as fallback / redundancy
IN_MEMORY_OTPS = {}
in_memory_lock = threading.Lock()

def _find_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "backend_api").exists():
            return parent
    return current.parent.parent
    
ROOT_DIR = _find_project_root()
DATA_DIR = ROOT_DIR / "backend_api" / "data"
DB_PATH = DATA_DIR / "otps.db"

def init_db():
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS otps (
                email TEXT PRIMARY KEY,
                otp_hash TEXT NOT NULL,
                expires_at REAL NOT NULL
            )
        """)
        conn.commit()
        conn.close()
        logger.info("[Forgot Password] [OTP Store] SQLite database initialized at %s", DB_PATH)
    except Exception as e:
        logger.error("[Forgot Password] [OTP Store] Failed to initialize SQLite database: %s", e)

init_db()

def _hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode('utf-8')).hexdigest()

def _get_user_id_by_email(email: str) -> str:
    """Helper to query user UUID from Supabase Admin users endpoint."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    email_clean = email.strip().lower()
    try:
        headers = {
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
        }
        resp = requests.get(
            f"{SUPABASE_URL.rstrip('/')}/auth/v1/admin/users",
            headers=headers,
            params={"page": 1, "per_page": 1000},
            timeout=10,
        )
        if resp.status_code == 200:
            users_data = resp.json()
            users = []
            if isinstance(users_data, list):
                users = users_data
            elif isinstance(users_data, dict):
                users = users_data.get("users", [])
            
            for u in users:
                u_email = (u.get("email") or "").strip().lower()
                if u_email == email_clean:
                    return u.get("id")
    except Exception as e:
        logger.error("[Forgot Password] [OTP Store] User UUID lookup failed: %s", e)
    return None

def generate_and_store_otp(email: str, expiry_minutes: int = 10) -> str:
    """
    Generate a cryptographically secure 6-digit OTP code and save it to Supabase.
    Falls back to SQLite & in-memory backup if Supabase write fails.
    """
    email_clean = email.lower().strip()
    otp = str(secrets.randbelow(900000) + 100000)
    otp_hash = _hash_otp(otp)
    now_ts = time.time()
    expires_ts = now_ts + (expiry_minutes * 60)
    
    # 1. Attempt writing to Supabase public.password_recovery_otps
    supabase_success = False
    if supabase_admin:
        try:
            user_id = _get_user_id_by_email(email_clean)
            expires_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=expiry_minutes)
            
            # Auto-prune expired OTPs in Supabase for cleanup
            try:
                now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
                supabase_admin.table("password_recovery_otps")\
                    .delete()\
                    .lt("expires_at", now_iso)\
                    .execute()
            except Exception as pe:
                logger.warning("[Forgot Password] [OTP Store] Supabase cleanup error: %s", pe)
            
            data = {
                "user_id": user_id,
                "email": email_clean,
                "otp_code": otp,
                "expires_at": expires_dt.isoformat(),
                "used": False
            }
            res = supabase_admin.table("password_recovery_otps").insert(data).execute()
            if res.data:
                logger.info("[Forgot Password] [OTP Store] OTP successfully stored in Supabase for %s", email_clean)
                supabase_success = True
        except Exception as e:
            logger.error("[Forgot Password] [OTP Store] Supabase insert failed: %s. Falling back to SQLite.", e)

    # 2. Local fallback storage (always store locally too for resilience and local testing)
    with in_memory_lock:
        IN_MEMORY_OTPS[email_clean] = {
            "otp_hash": otp_hash,
            "expires_at": expires_ts
        }
    
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO otps (email, otp_hash, expires_at) VALUES (?, ?, ?)",
                    (email_clean, otp_hash, expires_ts))
        conn.commit()
        conn.close()
        logger.info("[Forgot Password] [OTP Store] Local SQLite backup saved for %s", email_clean)
    except Exception as e:
        logger.error("[Forgot Password] [OTP Store] SQLite local backup failed: %s", e)
        
    return otp

def verify_and_consume_otp(email: str, otp: str) -> bool:
    """
    Verify the 6-digit OTP code for a user.
    Checks Supabase first, falling back to local SQLite/in-memory if not found.
    Marks code as used in Supabase (or deletes from local cache) on success.
    """
    email_clean = email.lower().strip()
    otp_hash = _hash_otp(otp)
    now_ts = time.time()
    now_dt = datetime.datetime.now(datetime.timezone.utc)
    
    # 1. Check Supabase first
    if supabase_admin:
        try:
            res = supabase_admin.table("password_recovery_otps")\
                .select("*")\
                .eq("email", email_clean)\
                .eq("otp_code", otp)\
                .eq("used", False)\
                .execute()
                
            if res.data:
                valid_rec = None
                for rec in res.data:
                    expires_str = rec["expires_at"].replace("Z", "+00:00")
                    expires_dt = datetime.datetime.fromisoformat(expires_str)
                    if expires_dt > now_dt:
                        valid_rec = rec
                        break
                
                if valid_rec:
                    # Invalidate/consume it in Supabase
                    supabase_admin.table("password_recovery_otps")\
                        .update({"used": True})\
                        .eq("id", valid_rec["id"])\
                        .execute()
                    
                    logger.info("[Forgot Password] [OTP Store] OTP verified successfully via Supabase for %s", email_clean)
                    
                    # Clean up local cache too
                    try:
                        with in_memory_lock:
                            IN_MEMORY_OTPS.pop(email_clean, None)
                        conn = sqlite3.connect(DB_PATH, timeout=5)
                        cur = conn.cursor()
                        cur.execute("DELETE FROM otps WHERE email = ?", (email_clean,))
                        conn.commit()
                        conn.close()
                    except Exception:
                        pass
                    return True
        except Exception as e:
            logger.error("[Forgot Password] [OTP Store] Supabase lookup failed: %s. Falling back to local cache.", e)

    # 2. Local fallback check
    logger.info("[Forgot Password] [OTP Store] checking local fallback for %s...", email_clean)
    with in_memory_lock:
        if email_clean in IN_MEMORY_OTPS:
            record = IN_MEMORY_OTPS[email_clean]
            if record["expires_at"] > now_ts and record["otp_hash"] == otp_hash:
                IN_MEMORY_OTPS.pop(email_clean, None)
                logger.info("[Forgot Password] [OTP Store] OTP verified successfully via in-memory store for %s", email_clean)
                
                try:
                    conn = sqlite3.connect(DB_PATH, timeout=5)
                    cur = conn.cursor()
                    cur.execute("DELETE FROM otps WHERE email = ?", (email_clean,))
                    conn.commit()
                    conn.close()
                except Exception:
                    pass
                return True

    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        cur.execute("DELETE FROM otps WHERE expires_at < ?", (now_ts,))
        cur.execute("SELECT otp_hash FROM otps WHERE email = ? AND expires_at > ?", (email_clean, now_ts))
        row = cur.fetchone()
        
        if row and row[0] == otp_hash:
            cur.execute("DELETE FROM otps WHERE email = ?", (email_clean,))
            conn.commit()
            conn.close()
            logger.info("[Forgot Password] [OTP Store] OTP verified successfully via local SQLite for %s", email_clean)
            return True
            
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error("[Forgot Password] [OTP Store] Local SQLite verify failed: %s", e)
        
    return False
