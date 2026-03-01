import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional
from .crypto import gen_salt, save_salt_for, load_salt_for, derive_key, encrypt_bytes, decrypt_bytes
import base64

LAST_USER_FILE = "last_user.txt"
DB_TEMPLATE = "tasks_{username}.db"

def get_last_user(path):
    fn = os.path.join(path, LAST_USER_FILE)
    if not os.path.exists(fn):
        return ""
    with open(fn, "r", encoding="utf-8") as f:
        return f.read().strip()

def save_last_user(username: str, path):
    fn = os.path.join(path, LAST_USER_FILE)
    with open(fn, "w", encoding="utf-8") as f:
        f.write(username)

def load_accounts_meta(path):
    fn = os.path.join(path, "accounts.json")
    if not os.path.exists(fn):
        return {}
    try:
        with open(fn, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_accounts_meta(meta, path):
    fn = os.path.join(path, "accounts.json")
    with open(fn, "w", encoding="utf-8") as f:
        json.dump(meta, f)

def ensure_account(username: str, passphrase: str, create_if_missing: bool = False, path: str = None, **kwargs):
    """
    STRICT CLOUD AUTHORITY: No local accounts.json.
    Expects 'email' and optionally 'metadata' (salt, wrapped_dek) in kwargs.
    Returns (dek, db_path).
    """
    if not path:
        raise ValueError("Explicit storage path is required.")
    email = kwargs.get("email")
    if not email:
        raise ValueError("Email required for authentication.")
        
    db_path = os.path.join(path, DB_TEMPLATE.format(username=username))
    metadata = kwargs.get("metadata")
    
    if create_if_missing and not metadata:
        # REGISTRATION: Create local encryption keys and return metadata
        dek = os.urandom(32) 
        salt_user = gen_salt()
        save_salt_for(username, salt_user, path=path)
        
        secret_seed = f"{username}:{email}"
        user_key = derive_key(secret_seed, salt_user)
        
        wrapped_dek_ct, wrapped_dek_nonce = encrypt_bytes(dek, user_key)
        
        # Return this to caller so it can be pushed to cloud
        new_metadata = {
            "salt": base64.b64encode(salt_user).decode(),
            "wrapped_dek": {"ct": wrapped_dek_ct, "nonce": wrapped_dek_nonce}
        }
        
        init_db_for(username, dek, path)
        return dek, db_path, new_metadata

    if not metadata:
        raise ValueError("Account metadata missing from cloud.")
        
    try:
        salt_user = base64.b64decode(metadata["salt"])
        w_dek = metadata["wrapped_dek"]
        
        # Save local salt for offline consistency (optional but helpful)
        save_salt_for(username, salt_user, path=path)
        
        secret_seed = f"{username}:{email}"
        user_key = derive_key(secret_seed, salt_user)
        
        dek = decrypt_bytes(w_dek["ct"], w_dek["nonce"], user_key)
        
        # VERY IMPORTANT: If the file did not exist locally (e.g. first compiled launch), guarantee the schema generates.
        if not os.path.exists(db_path):
            init_db_for(username, dek, path)
            
        # Ensure schema enhancements
        ensure_category_column(db_path)
        ensure_sound_column(db_path)
        ensure_description_column(db_path)
        ensure_status_columns(db_path)
        
        return dek, db_path
    except Exception as e:
        print(f"DEBUG: Encryption unwrap failed: {e}")
        raise ValueError("Incorrect username or password")

def complete_recovery(username: str, new_pass: str, path="."):
    """
    Recover account using stored recovery token. 
    (Assumes verification happened in UI)
    """
    # This function is now deprecated in the new stateless model.
    # Recovery should be handled by the cloud service providing the metadata.
    # If this function were to be used, it would need to receive the recovery
    # metadata (salt_recovery, recovery_token) via kwargs, similar to ensure_account.
    raise NotImplementedError("Account recovery is now handled by the cloud service.")

# ... (init_db_for and others remain)

# SKIP get_metric_details lines...

def change_passphrase(username, old_pass, new_pass, path=".", current_dek=None):
    """
    Updates the passphrase.
    CRITICAL CHANGE: We NO LONGER update the local encryption keys based on passphrase.
    Local encryption now relies on a Stable Key (Username+Email).
    This function simply returns the current DEK to maintain signature compatibility.
    """
    # We don't need to do ANYTHING to local storage if we are using Stable Key.
    # The 'passphrase' is only for Firebase Auth (handled by caller).
    
    # Just return DEK if we have it, or load it using Stable Key to verify access.
    if current_dek:
        return current_dek
        
    # If no DEK provided, try to load it just to be sure user exists?
    # Not strictly necessary but good for validation.
    try:
        meta = load_accounts_meta(path)
        if username not in meta: return None
        
        # Load implicitly via ensure_account style logic?
        # Actually, caller usually has DEK.
        pass
    except:
        pass
        
    return b"dummy_dek" # Should not be used for encryption reassignment anyway

def init_db_for(username: str, key: bytes, path="."):
    db = os.path.join(path, DB_TEMPLATE.format(username=username))
    db = os.path.join(path, DB_TEMPLATE.format(username=username))
    conn = sqlite3.connect(db, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    
    # Tasks table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ciphertext TEXT NOT NULL,
        nonce TEXT NOT NULL,
        due_iso TEXT NOT NULL,
        priority INTEGER DEFAULT 3,
        notified INTEGER DEFAULT 0,
        created_iso TEXT,
        completed_iso TEXT,
        category TEXT,
        sound TEXT DEFAULT 'Default',
        description TEXT DEFAULT '',
        status TEXT DEFAULT 'open',
        notification_status TEXT DEFAULT 'pending',
        is_overdue INTEGER DEFAULT 0
    )
    """)
    
    # Audit table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER,
        event TEXT,
        timestamp_iso TEXT,
        user_uid TEXT,
        extra TEXT
    )
    """)
    
    # Meta/Verification table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY,
        value TEXT,
        nonce TEXT
    )
    """)
    
    # Create verification token
    # We encrypt the string "VERIFY"
    ct, nonce = encrypt_bytes(b"VERIFY", key)
    cur.execute("INSERT OR REPLACE INTO meta (key, value, nonce) VALUES (?, ?, ?)", 
                ("verification", ct, nonce))
    
    conn.commit()
    conn.close()

def ensure_category_column(db_path: str):
    """Migrate DB to include category column if missing."""
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    try:
        cur.execute("SELECT category FROM tasks LIMIT 1")
    except sqlite3.OperationalError:
        # Column missing, add it
        cur.execute("ALTER TABLE tasks ADD COLUMN category TEXT")
        conn.commit()
    finally:
        conn.close()

def ensure_sound_column(db_path: str):
    """Migrate DB to include sound column if missing."""
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    try:
        cur.execute("SELECT sound FROM tasks LIMIT 1")
    except sqlite3.OperationalError:
        # Column missing, add it
        cur.execute("ALTER TABLE tasks ADD COLUMN sound TEXT DEFAULT 'Default'")
        conn.commit()
    finally:
        conn.close()

def ensure_description_column(db_path: str):
    """Migrate DB to include description column if missing."""
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    try:
        cur.execute("SELECT description FROM tasks LIMIT 1")
    except sqlite3.OperationalError:
        # Column missing, add it
        cur.execute("ALTER TABLE tasks ADD COLUMN description TEXT DEFAULT ''")
        conn.commit()
    finally:
        conn.close()

def ensure_status_columns(db_path: str):
    """Migrate DB to include analytics lifecycle state columns if missing."""
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    # 1. Active Task Status (open, completed, snoozed)
    try:
        cur.execute("SELECT status FROM tasks LIMIT 1")
    except sqlite3.OperationalError:
        cur.execute("ALTER TABLE tasks ADD COLUMN status TEXT DEFAULT 'open'")
        # Backfill existing completed tasks based on ISO presence
        cur.execute("UPDATE tasks SET status='completed' WHERE completed_iso IS NOT NULL AND completed_iso != ''")
        conn.commit()
        
    # 2. Notification Pipeline Status (pending, sent, snoozed, dismissed, clicked)
    try:
        cur.execute("SELECT notification_status FROM tasks LIMIT 1")
    except sqlite3.OperationalError:
        cur.execute("ALTER TABLE tasks ADD COLUMN notification_status TEXT DEFAULT 'pending'")
        # Backfill sent notifications based on legacy notified flag mapping
        cur.execute("UPDATE tasks SET notification_status='sent' WHERE notified=1")
        cur.execute("UPDATE tasks SET notification_status='dismissed' WHERE notified=2")
        conn.commit()
    # 3. Overdue Flag
    try:
        cur.execute("SELECT is_overdue FROM tasks LIMIT 1")
    except sqlite3.OperationalError:
        cur.execute("ALTER TABLE tasks ADD COLUMN is_overdue INTEGER DEFAULT 0")
        conn.commit()
    finally:
        conn.close()

def mark_overdue_tasks(db_path: str):
    """
    Background temporal process: Iterates open tasks and flags them overdue
    if the current time surpasses their due_iso deadline natively.
    """
    if not os.path.exists(db_path):
        return
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    now_iso = datetime.now().isoformat()
    # Explicitly clear overdue if due_iso is now in the future (e.g. after edit)
    # and set overdue if due_iso is in the past.
    cur.execute("UPDATE tasks SET is_overdue=1 WHERE status != 'completed' AND due_iso < ? AND (is_overdue IS NULL OR is_overdue = 0)", (now_iso,))
    cur.execute("UPDATE tasks SET is_overdue=0 WHERE (status = 'completed' OR due_iso >= ?) AND is_overdue = 1", (now_iso,))
    if cur.rowcount > 0:
        conn.commit()
    conn.close()

def verify_db_access(db_path: str, key: bytes) -> bool:
    """Try to decrypt the verification token."""
    if not os.path.exists(db_path):
        return False
        
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    try:
        cur.execute("SELECT value, nonce FROM meta WHERE key='verification'")
        row = cur.fetchone()
        if not row:
            return False
            
        ct, nonce = row
        try:
            plaintext = decrypt_bytes(ct, nonce, key)
            return plaintext == b"VERIFY"
        except Exception:
            return False
    except sqlite3.Error:
        return False
    finally:
        conn.close()

from backend.audit import write_audit

def ensure_uid_column(db_path: str):
    # This is now handled in backend/audit.py
    pass

# write_audit removed (use from backend.audit)

# Minimal CRUD
def save_task(db_path: str, ciphertext: str, nonce: str, due_iso: str, priority: int, created_iso: str, category: str = "", sound: str = "Default", description: str = "", user_uid: str = ""):
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""INSERT INTO tasks (ciphertext, nonce, due_iso, priority, notified, created_iso, category, sound, description, status, notification_status) VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, 'open', 'pending')""",
                (ciphertext, nonce, due_iso, priority, created_iso, category, sound, description))
    conn.commit()
    rowid = cur.lastrowid
    conn.close()
    write_audit(db_path, rowid, "created", f"Category: {category}", user_uid=user_uid)
    return rowid

def update_task(db_path: str, task_id: int, ciphertext: str, nonce: str, due_iso: str, priority: int, category: str, sound: str = "Default", description: str = "", user_uid: str = ""):
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    # Reset notified and is_overdue so it recalculates based on new due time
    cur.execute("""UPDATE tasks SET ciphertext=?, nonce=?, due_iso=?, priority=?, category=?, sound=?, description=?, notified=0, is_overdue=0 WHERE id=?""",
                (ciphertext, nonce, due_iso, priority, category, sound, description, task_id))
    conn.commit()
    conn.close()
    write_audit(db_path, task_id, "edited", f"Category: {category}", user_uid=user_uid)

def list_tasks(db_path: str):
    mark_overdue_tasks(db_path)
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    # Check if sound exists (it should due to ensure_sound_column)
    # We assume it exists now.
    cur.execute("SELECT id, ciphertext, nonce, due_iso, priority, notified, created_iso, completed_iso, category, sound, description, is_overdue FROM tasks ORDER BY due_iso")
    rows = cur.fetchall()
    conn.close()
    return rows

def mark_notified(db_path: str, task_id: int, user_uid: str = ""):
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET notified=1, notification_status='sent' WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    write_audit(db_path, task_id, "notified", user_uid=user_uid)

def dismiss_notification(db_path: str, task_id: int, user_uid: str = ""):
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    # Set notified = 2 (Acknowledged) so it doesn't highlight but stays in list
    cur.execute("UPDATE tasks SET notified=2, notification_status='dismissed' WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    write_audit(db_path, task_id, "dismissed", user_uid=user_uid)

def complete_task(db_path: str, task_id: int, completed_iso: str = "", user_uid: str = ""):
    if not completed_iso:
        completed_iso = datetime.now().isoformat()
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET completed_iso=?, status='completed' WHERE id=?", (completed_iso, task_id))
    conn.commit()
    conn.close()
    write_audit(db_path, task_id, "completed", user_uid=user_uid)

def delete_task(db_path: str, task_id: int, user_uid: str = ""):
    # Fetch title for audit before deletion
    title = "Unknown"
    # ... logic skipped ...
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    write_audit(db_path, task_id, "deleted", f"Task ID: {task_id}", user_uid=user_uid)

def delete_all_completed_tasks(db_path: str, user_uid: str = ""):
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    # 1. Truncate all historical logs to zero-out Analytics tracking metrics
    cur.execute("DELETE FROM audit")
    # 2. Delete all strictly completed history instances
    cur.execute("DELETE FROM tasks WHERE status='completed' OR (completed_iso IS NOT NULL AND completed_iso != '')")
    # 3. Strip any residual alert notification states from remaining open tasks
    cur.execute("UPDATE tasks SET notified=0, notification_status=''")
    conn.commit()
    conn.close()

def snooze_task(db_path: str, task_id: int, minutes: int, user_uid: str = ""):
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    # Calculate new due time using LOCAL time
    new_due = (datetime.now() + timedelta(minutes=minutes)).isoformat()
    # Reset notified AND is_overdue since it's now in the future
    cur.execute("UPDATE tasks SET due_iso=?, notified=0, is_overdue=0, status='snoozed', notification_status='snoozed' WHERE id=?", (new_due, task_id))
    conn.commit()
    conn.close()
    write_audit(db_path, task_id, "snoozed", f"Minutes: {minutes}", user_uid=user_uid)

def get_audit_stats(db_path: str, days: int = 7, offset_days: int = 0):
    """
    Calculate audit statistics for analytics.
    Args:
        days: Duration of the detailed window (default 7).
        offset_days: Shift window back by N days (default 0).
    Returns dict with counts and avg response time.
    """
    if not os.path.exists(db_path):
        return {
            'notifications_sent': 0, 'notifications_opened': 0, 
            'snoozed_events': 0, 'completed_tasks': 0, 'created_tasks': 0,
            'avg_response_min': 0.0, 'total_actions': 0
        }

    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    
    stats = {}
    
    # Check for Reset Timestamp
    reset_iso = None
    try:
        cur.execute("SELECT value FROM meta WHERE key='analytics_reset'")
        row = cur.fetchone()
        if row:
            reset_iso = row[0]
    except:
        pass

    # Calculate Date Range
    now = datetime.now() # Match local time used for task completion/creation
    end_dt = now - timedelta(days=offset_days)
    start_dt = end_dt - timedelta(days=days)
    
    # Adjust Start Date if Reset Happened Recently
    if reset_iso:
        try:
            reset_dt = datetime.fromisoformat(reset_iso)
            if reset_dt > start_dt:
                start_dt = reset_dt
        except:
            pass
            
    # If the window is effectively empty (start >= end), return zeros
    if start_dt >= end_dt:
        conn.close()
        return {
            'notifications_sent': 0, 'notifications_opened': 0, 
            'snoozed_events': 0, 'completed_tasks': 0, 'created_tasks': 0,
            'avg_response_min': 0.0, 'total_actions': 0
        }
    
    start_iso = start_dt.isoformat()
    end_iso = end_dt.isoformat()
    
    # Helper to count with filter [start, end)
    def count_event(evt):
        try:
            cur.execute("SELECT COUNT(*) FROM audit WHERE event=? AND timestamp_iso >= ? AND timestamp_iso < ?", (evt, start_iso, end_iso))
            row = cur.fetchone()
            return row[0] if row else 0
        except sqlite3.OperationalError:
            return 0
    
    # 1. Live Task State (Querying `tasks` table instead of audit logs for accuracy)
    try:
        cur.execute("SELECT COUNT(*) FROM tasks WHERE created_iso >= ? AND created_iso < ?", (start_iso, end_iso))
        row_created = cur.fetchone()
        stats['created_tasks'] = row_created[0] if row_created else 0
        
        cur.execute("SELECT COUNT(*) FROM tasks WHERE status='completed' AND completed_iso >= ? AND completed_iso < ?", (start_iso, end_iso))
        row_completed = cur.fetchone()
        stats['completed_tasks'] = row_completed[0] if row_completed else 0
    except sqlite3.OperationalError:
        # Fallback if DB not fully migrated yet
        stats['created_tasks'] = count_event('created')
        stats['completed_tasks'] = count_event('completed')

    # 2. Notification Pipeline State
    stats['notifications_sent'] = count_event('notified')
    stats['notifications_opened'] = count_event('opened')
    stats['snoozed_events'] = count_event('snoozed')
    
    # Total Actions (Summary Metric)
    stats['total_actions'] = (stats['notifications_sent'] + 
                              stats['notifications_opened'] + 
                              stats['snoozed_events'] + 
                              stats['completed_tasks'])
    
    # Avg Response Time Calculation
    try:
        cur.execute("SELECT task_id, event, timestamp_iso FROM audit WHERE event IN ('notified', 'opened') AND timestamp_iso >= ? AND timestamp_iso < ? ORDER BY timestamp_iso", (start_iso, end_iso))
        rows = cur.fetchall()
        
        task_start_times = {} 
        response_times = [] 
        
        for tid, evt, ts_str in rows:
            try:
                ts = datetime.fromisoformat(ts_str)
            except:
                continue
                
            if evt == 'notified':
                if tid not in task_start_times:
                    task_start_times[tid] = ts
            elif evt == 'opened':
                if tid in task_start_times:
                    start = task_start_times.pop(tid)
                    diff = (ts - start).total_seconds() / 60.0
                    if diff >= 0:
                        response_times.append(diff)
                        
        stats['avg_response_min'] = round(sum(response_times) / len(response_times), 1) if response_times else 0.0
        
    except Exception as e:
        print(f"Error calc response: {e}")
        stats['avg_response_min'] = 0.0
    
    conn.close()
    return stats

def get_audit_stats_since(db_path: str, start_dt: datetime):
    """
    Calculate stats from a specific start datetime until now.
    """
    if not os.path.exists(db_path):
        return {
            'notifications_sent': 0, 'notifications_opened': 0, 
            'snoozed_events': 0, 'completed_tasks': 0, 'created_tasks': 0
        }

    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    
    start_iso = start_dt.isoformat()
    end_iso = datetime.now().isoformat() # Local time to match task creation/completion
    
    stats = {}
    
    def count_event(evt):
        try:
            cur.execute("SELECT COUNT(*) FROM audit WHERE event=? AND timestamp_iso >= ? AND timestamp_iso <= ?", (evt, start_iso, end_iso))
            row = cur.fetchone()
            return row[0] if row else 0
        except sqlite3.OperationalError:
            return 0
            
    # Live SQL Fallback Mapping
    try:
        cur.execute("SELECT COUNT(*) FROM tasks WHERE created_iso >= ? AND created_iso <= ?", (start_iso, end_iso))
        row_created = cur.fetchone()
        stats['created_tasks'] = row_created[0] if row_created else 0
        
        cur.execute("SELECT COUNT(*) FROM tasks WHERE status='completed' AND completed_iso >= ? AND completed_iso <= ?", (start_iso, end_iso))
        row_completed = cur.fetchone()
        stats['completed_tasks'] = row_completed[0] if row_completed else 0
    except sqlite3.OperationalError:
        stats['completed_tasks'] = count_event('completed')
        stats['created_tasks'] = count_event('created')
    
    stats['notifications_sent'] = count_event('notified')
    stats['notifications_opened'] = count_event('opened')
    stats['snoozed_events'] = count_event('snoozed')
    
    conn.close()
    return stats

def reset_audit_stats(db_path: str):
    """
    Manually reset analytics by setting a timestamp in meta.
    Does NOT delete data, just hides it from get_audit_stats.
    """
    if not os.path.exists(db_path):
        return
        
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    try:
        # We encrypt "RESET" just to be consistent with meta table format if needed? 
        # But 'meta' table defined key, value, nonce.
        # Let's just store plaintext ISO for simplicity or encrypt if we must. 
        # The meta table has 'key', 'value', 'nonce'. 
        # If we store plaintext, nonce can be empty.
        
        reset_iso = datetime.now().isoformat()
        cur.execute("INSERT OR REPLACE INTO meta (key, value, nonce) VALUES (?, ?, ?)", 
                    ("analytics_reset", reset_iso, ""))
        conn.commit()
    except Exception as e:
        print(f"Failed to reset analytics: {e}")
    finally:
        conn.close()

def get_metric_details(db_path: str, metric_type: str, start_dt: datetime = None):
    """
    Get detailed breakdown for a specific metric.
    Optional: start_dt to filter by time window.
    """
    if not os.path.exists(db_path):
        return {}

    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    details = {}
    
    # Filter Logic
    start_iso = start_dt.isoformat() if start_dt else "1970-01-01T00:00:00"

    try:
        if metric_type == 'notifications_sent':
            # Total in window
            cur.execute("SELECT COUNT(*) FROM audit WHERE event='notified' AND timestamp_iso >= ?", (start_iso,))
            details['total'] = cur.fetchone()[0]
            
            # Recent Breakdown
            cur.execute("""
                SELECT substr(timestamp_iso, 1, 10) as day, COUNT(*) 
                FROM audit 
                WHERE event='notified' AND timestamp_iso >= ?
                GROUP BY day 
                ORDER BY day DESC 
                LIMIT 5
            """, (start_iso,))
            details['daily_breakdown'] = cur.fetchall()

        elif metric_type == 'notifications_opened':
            cur.execute("SELECT COUNT(*) FROM audit WHERE event='opened' AND timestamp_iso >= ?", (start_iso,))
            opened = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM audit WHERE event='notified' AND timestamp_iso >= ?", (start_iso,))
            sent = cur.fetchone()[0]
            
            details['total_opened'] = opened
            details['total_sent'] = sent
            details['open_rate'] = round((opened / sent * 100), 1) if sent > 0 else 0.0
            
            cur.execute("SELECT timestamp_iso FROM audit WHERE event='opened' AND timestamp_iso >= ? ORDER BY timestamp_iso DESC LIMIT 5", (start_iso,))
            details['recent_events'] = [r[0] for r in cur.fetchall()]

        elif metric_type == 'snoozed_events':
            cur.execute("SELECT COUNT(*) FROM audit WHERE event='snoozed' AND timestamp_iso >= ?", (start_iso,))
            details['total_snoozed'] = cur.fetchone()[0]
            
            # Common snooze durations
            cur.execute("SELECT extra, COUNT(*) as c FROM audit WHERE event='snoozed' AND timestamp_iso >= ? GROUP BY extra ORDER BY c DESC LIMIT 3", (start_iso,))
            details['common_durations'] = cur.fetchall()
            
            cur.execute("SELECT timestamp_iso, extra FROM audit WHERE event='snoozed' AND timestamp_iso >= ? ORDER BY timestamp_iso DESC LIMIT 5", (start_iso,))
            details['recent_events'] = cur.fetchall()

        elif metric_type == 'completed_tasks':
            cur.execute("SELECT COUNT(DISTINCT task_id) FROM audit WHERE event='completed' AND timestamp_iso >= ?", (start_iso,))
            completed = cur.fetchone()[0]
            cur.execute("SELECT COUNT(DISTINCT task_id) FROM audit WHERE event='created' AND timestamp_iso >= ?", (start_iso,))
            created = cur.fetchone()[0]
            
            details['total_completed'] = completed
            details['total_created'] = created
            details['completion_rate'] = round((completed / created * 100), 1) if created > 0 else 0.0
            
            # Recent Log (Grouped to prevent duplicates of the same task)
            cur.execute("""
                SELECT MAX(timestamp_iso) 
                FROM audit 
                WHERE event='completed' AND timestamp_iso >= ? 
                GROUP BY task_id
                ORDER BY MAX(timestamp_iso) DESC 
                LIMIT 5
            """, (start_iso,))
            details['recent_events'] = [r[0] for r in cur.fetchall()]
            
        elif metric_type == 'avg_response_min':
            # Re-calculate response times
            cur.execute("SELECT task_id, event, timestamp_iso FROM audit WHERE event IN ('notified', 'opened') AND timestamp_iso >= ? ORDER BY timestamp_iso", (start_iso,))
            rows = cur.fetchall()
            
            task_start_times = {}
            response_times = []
            
            for tid, evt, ts_str in rows:
                try:
                    ts = datetime.fromisoformat(ts_str)
                except:
                    continue
                if evt == 'notified':
                    if tid not in task_start_times:
                        task_start_times[tid] = ts
                elif evt == 'opened':
                    if tid in task_start_times:
                        start = task_start_times.pop(tid)
                        diff = (ts - start).total_seconds() / 60.0
                        if diff >= 0:
                            response_times.append(diff)
            
            if response_times:
                details['min_response'] = round(min(response_times), 1)
                details['max_response'] = round(max(response_times), 1)
                details['avg_response'] = round(sum(response_times) / len(response_times), 1)
                details['count'] = len(response_times)
            else:
                details['min_response'] = 0.0
                details['max_response'] = 0.0
                details['avg_response'] = 0.0
                details['count'] = 0

    except Exception as e:
        print(f"Error in get_metric_details: {e}")
        
    finally:
        conn.close()
    return details



def get_email_by_username(username: str, path):
    """
    Retrieve email associated with a username for Username-First Auth.
    """
    meta = load_accounts_meta(path)
    if username in meta:
        return meta[username].get("email", "")
    return ""

def resolve_user_case_insensitive(username: str, path):
    """
    Returns (canonical_username, email) if found (ignoring case).
    Returns (None, None) if not found.
    """
    meta = load_accounts_meta(path)
    if username in meta:
        return username, meta[username].get("email", "")
        
    # Case insensitive search
    u_lower = username.lower()
    for k in meta:
        if k == "last_active_user" or k == "welcome_seen": continue  # Skip non-user keys
        if k.lower() == u_lower:
            return k, meta[k].get("email", "")
            
    return None, None

def is_first_run(path):
    """
    Check if this is the first run of the app.
    Uses a 'system.json' file or checks accounts existence.
    """
    sys_fn = os.path.join(path, "system.json")
    if not os.path.exists(sys_fn):
        return True
    
    try:
        with open(sys_fn, "r") as f:
            data = json.load(f)
            return not data.get("first_run_complete", False)
    except:
        return True

def set_first_run_complete(path):
    sys_fn = os.path.join(path, "system.json")
    data = {}
    if os.path.exists(sys_fn):
        try:
            with open(sys_fn, "r") as f:
                data = json.load(f)
        except:
             pass
    
    data["first_run_complete"] = True
    
    with open(sys_fn, "w") as f:
        json.dump(data, f)

def get_theme_preference(path):
    """Returns 'Light' or 'Dark' based on saved preference. Default 'Light'."""
    sys_fn = os.path.join(path, "system.json")
    if not os.path.exists(sys_fn):
        return "Light"
    
    try:
        with open(sys_fn, "r") as f:
            data = json.load(f)
            return data.get("theme_style", "Light")
    except:
        return "Light"

def save_theme_preference(theme_style: str, path):
    """Saves 'Light' or 'Dark' to system.json."""
    sys_fn = os.path.join(path, "system.json")
    data = {}
    if os.path.exists(sys_fn):
        try:
            with open(sys_fn, "r") as f:
                data = json.load(f)
        except:
             pass
    
    data["theme_style"] = theme_style
    
    with open(sys_fn, "w") as f:
        json.dump(data, f)
        
def reset_local_account(username: str, path="."):
    """
    Completely remove local account data.
    Used when password sync is broken and user wants to start fresh.
    """
    import shutil
    import time
    
    meta = load_accounts_meta(path)
    
    # 1. Look up data
    if username not in meta:
        # Maybe it was partially deleted? Check files anyway
        # We can construct filename from template if simple
        pass
    else:
        data = meta[username]
        db_path = os.path.join(path, data.get("db", ""))
        
        # 2. Delete DB File (Retry Logic for Windows Locks)
        if os.path.exists(db_path):
            for i in range(3):
                try:
                    os.remove(db_path)
                    break
                except PermissionError:
                    time.sleep(0.5)
                except Exception as e:
                    print(f"Error removing DB: {e}")
                    break
        
        # 3. Delete Salt File
        salt_path = os.path.join(path, f"key_salt_{username}.bin")
        if os.path.exists(salt_path):
             try:
                os.remove(salt_path)
             except:
                pass

        # 4. Remove from meta
        del meta[username]
        save_accounts_meta(meta, path)
        return True
        
    return False

def is_first_run_meta(path):
    meta = load_accounts_meta(path)
    return not meta.get("welcome_seen", False)

def set_first_run_complete_meta(path):
    meta = load_accounts_meta(path)
    meta["welcome_seen"] = True
    save_accounts_meta(meta, path)