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
    if not path:
        raise ValueError("Explicit storage path is required.")
    email = kwargs.get("email")
    if not email:
        raise ValueError("Email required for authentication.")
        
    db_path = os.path.join(path, DB_TEMPLATE.format(username=username))
    metadata = kwargs.get("metadata")
    
    if create_if_missing and not metadata:
        dek = os.urandom(32) 
        salt_user = gen_salt()
        save_salt_for(username, salt_user, path=path)
        
        secret_seed = f"{username}:{email}"
        user_key = derive_key(secret_seed, salt_user)
        
        wrapped_dek_ct, wrapped_dek_nonce = encrypt_bytes(dek, user_key)
        
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
        
        save_salt_for(username, salt_user, path=path)
        
        secret_seed = f"{username}:{email}"
        user_key = derive_key(secret_seed, salt_user)
        
        dek = decrypt_bytes(w_dek["ct"], w_dek["nonce"], user_key)
        
        if not os.path.exists(db_path):
            init_db_for(username, dek, path)
        else:
            # Ensure all tables exist even if the file is there
            init_db_for(username, dek, path)
            
        ensure_category_column(db_path)
        ensure_sound_column(db_path)
        ensure_description_column(db_path)
        ensure_status_columns(db_path)
        
        return dek, db_path
    except Exception as e:
        print(f"DEBUG: Encryption unwrap failed: {e}")
        raise ValueError("Incorrect username or password")

def init_db_for(username: str, key: bytes, path="."):
    db = os.path.join(path, DB_TEMPLATE.format(username=username))
    conn = sqlite3.connect(db, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    
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
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY,
        value TEXT,
        nonce TEXT
    )
    """)
    
    ct, nonce = encrypt_bytes(b"VERIFY", key)
    cur.execute("INSERT OR REPLACE INTO meta (key, value, nonce) VALUES (?, ?, ?)", 
                ("verification", ct, nonce))
    
    conn.commit()
    conn.close()

def ensure_category_column(db_path: str):
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    try:
        cur.execute("SELECT category FROM tasks LIMIT 1")
    except sqlite3.OperationalError:
        cur.execute("ALTER TABLE tasks ADD COLUMN category TEXT")
        conn.commit()
    finally:
        conn.close()

def ensure_sound_column(db_path: str):
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    try:
        cur.execute("SELECT sound FROM tasks LIMIT 1")
    except sqlite3.OperationalError:
        cur.execute("ALTER TABLE tasks ADD COLUMN sound TEXT DEFAULT 'Default'")
        conn.commit()
    finally:
        conn.close()

def ensure_description_column(db_path: str):
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    try:
        cur.execute("SELECT description FROM tasks LIMIT 1")
    except sqlite3.OperationalError:
        cur.execute("ALTER TABLE tasks ADD COLUMN description TEXT DEFAULT ''")
        conn.commit()
    finally:
        conn.close()

def ensure_status_columns(db_path: str):
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    try:
        cur.execute("SELECT status FROM tasks LIMIT 1")
    except sqlite3.OperationalError:
        cur.execute("ALTER TABLE tasks ADD COLUMN status TEXT DEFAULT 'open'")
        cur.execute("UPDATE tasks SET status='completed' WHERE completed_iso IS NOT NULL AND completed_iso != ''")
        conn.commit()
        
    try:
        cur.execute("SELECT notification_status FROM tasks LIMIT 1")
    except sqlite3.OperationalError:
        cur.execute("ALTER TABLE tasks ADD COLUMN notification_status TEXT DEFAULT 'pending'")
        cur.execute("UPDATE tasks SET notification_status='sent' WHERE notified=1")
        cur.execute("UPDATE tasks SET notification_status='dismissed' WHERE notified=2")
        conn.commit()
    try:
        cur.execute("SELECT is_overdue FROM tasks LIMIT 1")
    except sqlite3.OperationalError:
        cur.execute("ALTER TABLE tasks ADD COLUMN is_overdue INTEGER DEFAULT 0")
        conn.commit()
    finally:
        conn.close()

def mark_overdue_tasks(db_path: str):
    if not os.path.exists(db_path):
        return
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    now_iso = datetime.now().isoformat()
    cur.execute("""
        SELECT id FROM tasks
        WHERE status != 'completed'
          AND due_iso < ?
          AND (is_overdue IS NULL OR is_overdue = 0)
    """, (now_iso,))
    newly_missed = [row[0] for row in cur.fetchall()]

    cur.execute("""
        UPDATE tasks
        SET is_overdue=1, notification_status='missed'
        WHERE status != 'completed'
          AND due_iso < ?
          AND (is_overdue IS NULL OR is_overdue = 0)
    """, (now_iso,))
    cur.execute("UPDATE tasks SET is_overdue=0 WHERE (status = 'completed' OR due_iso >= ?) AND is_overdue = 1", (now_iso,))
    conn.commit()
    conn.close()

    for task_id in newly_missed:
        write_audit(db_path, task_id, "missed", "Task deadline passed")

def verify_db_access(db_path: str, key: bytes) -> bool:
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
    cur.execute("""UPDATE tasks SET ciphertext=?, nonce=?, due_iso=?, priority=?, category=?, sound=?, description=?, notified=0, notification_status='pending', is_overdue=0 WHERE id=?""",
                (ciphertext, nonce, due_iso, priority, category, sound, description, task_id))
    conn.commit()
    conn.close()
    write_audit(db_path, task_id, "edited", f"Category: {category}", user_uid=user_uid)

def list_tasks(db_path: str):
    mark_overdue_tasks(db_path)
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("SELECT id, ciphertext, nonce, due_iso, priority, notified, created_iso, completed_iso, category, sound, description, is_overdue, status, notification_status FROM tasks ORDER BY due_iso")
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

def log_notification_event(db_path: str, task_id: int, event: str, extra: str = "", user_uid: str = ""):
    allowed = {
        "notification_scheduled": "scheduled",
        "notification_triggered": "sent",
        "opened": "opened",
        "dismissed": "dismissed",
        "notification_test": "test",
        "reminder_missed": "missed",
        "snoozed_from_notification": "snoozed",
        "completed_from_notification": "completed",
    }
    if event not in allowed:
        raise ValueError(f"Unsupported notification event: {event}")

    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()

    if event == "notification_scheduled":
        cur.execute("SELECT notification_status FROM tasks WHERE id=?", (task_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return False
        current_status = row[0] or ""
        if current_status in {"scheduled", "opened", "dismissed", "missed", "sent"}:
            conn.close()
            return False

    cur.execute(
        "UPDATE tasks SET notification_status=? WHERE id=?",
        (allowed[event], task_id),
    )
    conn.commit()
    conn.close()
    write_audit(db_path, task_id, event, extra, user_uid=user_uid)
    return True

def dismiss_notification(db_path: str, task_id: int, user_uid: str = ""):
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
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

def reopen_task(db_path: str, task_id: int, user_uid: str = ""):
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET completed_iso=NULL, status='open' WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    write_audit(db_path, task_id, "reopened", user_uid=user_uid)

def delete_task(db_path: str, task_id: int, user_uid: str = ""):
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    write_audit(db_path, task_id, "deleted", f"Task ID: {task_id}", user_uid=user_uid)

def delete_all_completed_tasks(db_path: str, user_uid: str = ""):
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE status='completed' OR (completed_iso IS NOT NULL AND completed_iso != '')")
    conn.commit()
    conn.close()

def delete_audit_log(db_path: str, log_id: int):
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("DELETE FROM audit WHERE id=?", (log_id,))
    conn.commit()
    conn.close()

def delete_all_audit_logs(db_path: str):
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("DELETE FROM audit")
    conn.commit()
    conn.close()

def snooze_task(db_path: str, task_id: int, minutes: int, user_uid: str = ""):
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    new_due = (datetime.now() + timedelta(minutes=minutes)).isoformat()
    cur.execute("""
        UPDATE tasks 
        SET due_iso=?, 
            notified=0, 
            is_overdue=0, 
            status='snoozed', 
            notification_status='snoozed',
            completed_iso=NULL 
        WHERE id=?
    """, (new_due, task_id))
    conn.commit()
    conn.close()
    write_audit(db_path, task_id, "snoozed", f"Minutes: {minutes}. Task reopened if completed.", user_uid=user_uid)

def get_audit_stats(db_path: str, days: int = 7, offset_days: int = 0):
    if not os.path.exists(db_path):
        return {
            'notifications_sent': 0, 'notifications_opened': 0, 
            'snoozed_events': 0, 'completed_tasks': 0, 'created_tasks': 0,
            'avg_response_min': 0.0, 'total_actions': 0
        }

    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    stats = {}
    reset_iso = None
    try:
        cur.execute("SELECT value FROM meta WHERE key='analytics_reset'")
        row = cur.fetchone()
        if row:
            reset_iso = row[0]
    except:
        pass

    now = datetime.now()
    end_dt = now - timedelta(days=offset_days)
    start_dt = end_dt - timedelta(days=days)
    if reset_iso:
        try:
            reset_dt = datetime.fromisoformat(reset_iso)
            if reset_dt > start_dt:
                start_dt = reset_dt
        except:
            pass
    if start_dt >= end_dt:
        conn.close()
        return {
            'notifications_sent': 0, 'notifications_opened': 0, 
            'snoozed_events': 0, 'completed_tasks': 0, 'created_tasks': 0,
            'avg_response_min': 0.0, 'total_actions': 0
        }
    
    start_iso = start_dt.isoformat()
    end_iso = end_dt.isoformat()
    def count_event(evt):
        try:
            cur.execute("SELECT COUNT(*) FROM audit WHERE event=? AND timestamp_iso >= ? AND timestamp_iso < ?", (evt, start_iso, end_iso))
            row = cur.fetchone()
            return row[0] if row else 0
        except sqlite3.OperationalError:
            return 0
    try:
        cur.execute("SELECT COUNT(*) FROM tasks WHERE created_iso >= ? AND created_iso < ?", (start_iso, end_iso))
        row_created = cur.fetchone()
        stats['created_tasks'] = row_created[0] if row_created else 0
        cur.execute("SELECT COUNT(*) FROM tasks WHERE status='completed' AND completed_iso >= ? AND completed_iso < ?", (start_iso, end_iso))
        row_completed = cur.fetchone()
        stats['completed_tasks'] = row_completed[0] if row_completed else 0
    except sqlite3.OperationalError:
        stats['created_tasks'] = count_event('created')
        stats['completed_tasks'] = count_event('completed')

    stats['notifications_sent'] = count_event('notified')
    stats['notifications_opened'] = count_event('opened')
    stats['snoozed_events'] = count_event('snoozed')
    stats['total_actions'] = (stats['notifications_sent'] + stats['notifications_opened'] + stats['snoozed_events'] + stats['completed_tasks'])
    
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
    except:
        stats['avg_response_min'] = 0.0
    conn.close()
    return stats

def get_audit_stats_since(db_path: str, start_dt: datetime):
    if not os.path.exists(db_path):
        return {'notifications_sent': 0, 'notifications_opened': 0, 'snoozed_events': 0, 'completed_tasks': 0, 'created_tasks': 0}
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    start_iso = start_dt.isoformat()
    end_iso = datetime.now().isoformat()
    stats = {}
    def count_event(evt):
        try:
            cur.execute("SELECT COUNT(*) FROM audit WHERE event=? AND timestamp_iso >= ? AND timestamp_iso <= ?", (evt, start_iso, end_iso))
            row = cur.fetchone()
            return row[0] if row else 0
        except sqlite3.OperationalError:
            return 0
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
    if not os.path.exists(db_path): return
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    try:
        reset_iso = datetime.now().isoformat()
        cur.execute("INSERT OR REPLACE INTO meta (key, value, nonce) VALUES (?, ?, ?)", ("analytics_reset", reset_iso, ""))
        conn.commit()
    except Exception as e:
        print(f"Failed to reset analytics: {e}")
    finally:
        conn.close()
