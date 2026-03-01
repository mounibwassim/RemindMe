import sqlite3
import os
from datetime import datetime

def ensure_uid_column(db_path: str):
    """Migrate audit table to include user_uid column if missing."""
    if not os.path.exists(db_path): return
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    try:
        cur.execute("SELECT user_uid FROM audit LIMIT 1")
    except sqlite3.OperationalError:
        try:
            cur.execute("ALTER TABLE audit ADD COLUMN user_uid TEXT")
            conn.commit()
        except:
            pass
    finally:
        conn.close()

def write_audit(db_path: str, task_id: int, event: str, extra: str = "", user_uid: str = "", task_title: str = ""):
    ensure_uid_column(db_path)
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("INSERT INTO audit (task_id, event, timestamp_iso, user_uid, extra) VALUES (?, ?, ?, ?, ?)",
                (task_id, event, datetime.now().isoformat(), user_uid, extra))
    conn.commit()
    conn.close()
    
    # 🚨 Cloud Sync
    if user_uid:
        from backend.auth_service import write_audit_cloud
        # If task_title is not passed, it might be harder to resolve here without querying DB,
        # but we can pass task_id as extra or simple reference.
        write_audit_cloud(user_uid, event, task_title=task_title, extra=extra)

def get_audit_logs(db_path: str, limit: int = 100, event_type: str = None):
    if not os.path.exists(db_path): return []
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    
    query = "SELECT id, task_id, event, timestamp_iso, user_uid, extra FROM audit"
    params = []
    
    if event_type:
        query += " WHERE event = ?"
        params.append(event_type)
        
    query += " ORDER BY timestamp_iso DESC LIMIT ?"
    params.append(limit)
    
    try:
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
    except sqlite3.OperationalError:
        # Fallback if migration hasn't run yet
        query = query.replace(", user_uid", "")
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        
    conn.close()
    return rows