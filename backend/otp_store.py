import sqlite3
import os
import time
import hashlib
import secrets
import logging
import threading
from pathlib import Path

logger = logging.getLogger("backend_api")

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

def generate_and_store_otp(email: str, expiry_minutes: int = 15) -> str:
    email_clean = email.lower().strip()
    otp = str(secrets.randbelow(900000) + 100000)
    otp_hash = _hash_otp(otp)
    expires_at = time.time() + (expiry_minutes * 60)
    
    logger.info("[Forgot Password] [OTP Store] Storing OTP hash in memory fallback for %s...", email_clean)
    with in_memory_lock:
        IN_MEMORY_OTPS[email_clean] = {
            "otp_hash": otp_hash,
            "expires_at": expires_at
        }
    
    logger.info("[Forgot Password] [OTP Store] Storing OTP hash in SQLite database for %s...", email_clean)
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        # Replace any existing OTP for this email
        cur.execute("INSERT OR REPLACE INTO otps (email, otp_hash, expires_at) VALUES (?, ?, ?)",
                    (email_clean, otp_hash, expires_at))
        conn.commit()
        conn.close()
        logger.info("[Forgot Password] [OTP Store] OTP successfully stored in SQLite for %s", email_clean)
    except Exception as e:
        logger.error("[Forgot Password] [OTP Store] SQLite write failed for %s, relying on in-memory store fallback. Error: %s", email_clean, e)
        
    return otp

def verify_and_consume_otp(email: str, otp: str) -> bool:
    email_clean = email.lower().strip()
    otp_hash = _hash_otp(otp)
    now = time.time()
    
    logger.info("[Forgot Password] [OTP Store] Checking in-memory store for OTP verification for %s...", email_clean)
    # Check memory first
    with in_memory_lock:
        # Prune expired keys in memory
        expired_keys = [k for k, v in IN_MEMORY_OTPS.items() if v["expires_at"] < now]
        for k in expired_keys:
            IN_MEMORY_OTPS.pop(k, None)
            logger.info("[Forgot Password] [OTP Store] Pruned expired in-memory OTP for %s", k)
            
        if email_clean in IN_MEMORY_OTPS:
            record = IN_MEMORY_OTPS[email_clean]
            if record["otp_hash"] == otp_hash:
                IN_MEMORY_OTPS.pop(email_clean, None)
                logger.info("[Forgot Password] [OTP Store] OTP verified successfully via in-memory store for %s", email_clean)
                
                # Consume from SQLite too if possible
                try:
                    conn = sqlite3.connect(DB_PATH, timeout=5)
                    cur = conn.cursor()
                    cur.execute("DELETE FROM otps WHERE email = ?", (email_clean,))
                    conn.commit()
                    conn.close()
                except Exception:
                    pass
                return True
            else:
                logger.warning("[Forgot Password] [OTP Store] OTP hash mismatch in-memory for %s", email_clean)

    logger.info("[Forgot Password] [OTP Store] Checking SQLite database for OTP verification for %s...", email_clean)
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        cur = conn.cursor()
        
        # Delete expired OTPs globally to clean up
        cur.execute("DELETE FROM otps WHERE expires_at < ?", (now,))
        
        cur.execute("SELECT otp_hash FROM otps WHERE email = ?", (email_clean,))
        row = cur.fetchone()
        
        if row and row[0] == otp_hash:
            # Valid OTP, consume it
            cur.execute("DELETE FROM otps WHERE email = ?", (email_clean,))
            conn.commit()
            conn.close()
            logger.info("[Forgot Password] [OTP Store] OTP verified successfully via SQLite for %s", email_clean)
            return True
            
        conn.commit()
        conn.close()
        logger.warning("[Forgot Password] [OTP Store] OTP verification failed in SQLite (invalid or expired) for %s", email_clean)
    except Exception as e:
        logger.error("[Forgot Password] [OTP Store] Failed to query/consume OTP from SQLite for %s. Error: %s", email_clean, e)
        
    return False

