import sqlite3
import os
import time
import hashlib
import secrets
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "backend_api" / "data"
DB_PATH = DATA_DIR / "otps.db"

def init_db():
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

init_db()

def _hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode('utf-8')).hexdigest()

def generate_and_store_otp(email: str, expiry_minutes: int = 15) -> str:
    # 6 digit OTP
    otp = str(secrets.randbelow(900000) + 100000)
    otp_hash = _hash_otp(otp)
    expires_at = time.time() + (expiry_minutes * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Replace any existing OTP for this email
    cur.execute("INSERT OR REPLACE INTO otps (email, otp_hash, expires_at) VALUES (?, ?, ?)",
                (email.lower().strip(), otp_hash, expires_at))
    conn.commit()
    conn.close()
    return otp

def verify_and_consume_otp(email: str, otp: str) -> bool:
    email_clean = email.lower().strip()
    otp_hash = _hash_otp(otp)
    now = time.time()
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # First, delete expired OTPs globally to clean up
    cur.execute("DELETE FROM otps WHERE expires_at < ?", (now,))
    
    cur.execute("SELECT otp_hash FROM otps WHERE email = ?", (email_clean,))
    row = cur.fetchone()
    
    if row and row[0] == otp_hash:
        # Valid OTP, consume it
        cur.execute("DELETE FROM otps WHERE email = ?", (email_clean,))
        conn.commit()
        conn.close()
        return True
        
    conn.commit()
    conn.close()
    return False
