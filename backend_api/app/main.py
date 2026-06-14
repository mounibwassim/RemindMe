# Force uvicorn reload to pick up backend/ai_assistant.py changes
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

# Set up logging (resilient to container permission restrictions)
log_file = None
if os.environ.get("APP_ENV") != "production":
    try:
        log_file = os.path.join(os.getcwd(), '..', 'backend_errors.log')
        with open(log_file, 'a'):
            pass
    except Exception:
        log_file = None

if log_file:
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
logger = logging.getLogger("backend_api")

from app.routers import assistant, auth, analytics, tasks

app = FastAPI(
    title="RemindMe Python API",
    version="0.1.0",
    description="Python business-logic API for the Flutter RemindMe client.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def health():
    return {
        "status": "ok",
        "service": "remindme-python-api",
        "git_commit": os.environ.get("RENDER_GIT_COMMIT", "unknown")
    }


@app.get("/")
async def root():
    return {"status": "online"}


from app.routers import assistant, auth, analytics, tasks, system

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(assistant.router, prefix="/api/v1/assistant", tags=["assistant"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])


@app.get("/api/v1/debug/latest-otp/{username}", tags=["debug"])
def get_latest_otp_debug(username: str):
    from backend.supabase_auth import get_username_data, supabase_admin
    import sqlite3
    import time
    from backend.otp_store import DB_PATH, IN_MEMORY_OTPS
    
    email = None
    if "@" in username:
        email = username.strip().lower()
    else:
        user_data, error = get_username_data(username)
        if user_data:
            email = user_data.get("email")
            
    if not email:
        return {"error": f"Username or email '{username}' not registered/found."}
        
    email_clean = email.strip().lower()
    
    # 1. Check Supabase password_recovery_otps table
    if supabase_admin:
        try:
            res = supabase_admin.table("password_recovery_otps")\
                .select("*")\
                .eq("email", email_clean)\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
            if res.data and len(res.data) > 0:
                record = res.data[0]
                return {
                    "source": "Supabase DB",
                    "username": username,
                    "email": email_clean,
                    "generated_otp": record.get("otp_code"),
                    "created_at": record.get("created_at"),
                    "expires_at": record.get("expires_at"),
                    "used": record.get("used")
                }
        except Exception:
            pass
            
    # 2. Check local SQLite fallback
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT otp_hash, expires_at FROM otps WHERE email = ? ORDER BY expires_at DESC LIMIT 1", (email_clean,))
        row = cur.fetchone()
        conn.close()
        if row:
            return {
                "source": "Local SQLite (hashed)",
                "username": username,
                "email": email_clean,
                "otp_hash": row[0],
                "expires_at": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(row[1])),
                "expired": bool(time.time() > row[1])
            }
    except Exception:
        pass
        
    # 3. Check in-memory store
    if email_clean in IN_MEMORY_OTPS:
        record = IN_MEMORY_OTPS[email_clean]
        return {
            "source": "In-Memory cache",
            "username": username,
            "email": email_clean,
            "otp_hash": record.get("otp_hash"),
            "expires_at": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(record.get("expires_at"))),
            "expired": bool(time.time() > record.get("expires_at"))
        }
        
    return {"error": f"No OTP record found for '{email_clean}'."}

