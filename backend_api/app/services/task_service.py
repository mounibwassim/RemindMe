from datetime import datetime, timedelta
from fastapi import HTTPException

from backend.crypto import decrypt_bytes, encrypt_bytes
import backend.supabase_service as supabase

from app.schemas import TaskCreateRequest, TaskResponse, TaskUpdateRequest
from app.services.session_store import UserSession


def _row_to_task(session: UserSession, row) -> TaskResponse:
    # Supabase row is a dict
    task_id = str(row["id"])
    encrypted_payload = row.get("encrypted_data")
    due_iso = row.get("due_iso")
    priority = row.get("priority", 2)
    category = row.get("category", "General")
    is_completed = row.get("is_completed", False)
    created_iso = row.get("created_at")
    
    title = "Encrypted Task"
    desc = ""
    
    if encrypted_payload and ":" in encrypted_payload:
        try:
            # Format: nonce:ciphertext (base64)
            nonce_b64, ct_b64 = encrypted_payload.split(":", 1)
            plaintext = decrypt_bytes(ct_b64, nonce_b64, session.key).decode("utf-8")
            if "\n" in plaintext:
                parts = plaintext.split("\n", 1)
                title = parts[0]
                desc = parts[1]
            else:
                title = plaintext
        except Exception as e:
            print(f"DEBUG: Decryption failed for task {task_id}: {e}")

    # Overdue logic using proper datetime objects
    is_overdue = 0
    if due_iso and not is_completed:
        try:
            # Normalize to UTC for comparison
            now_utc = datetime.utcnow()
            clean_due = due_iso.replace('Z', '+00:00')
            if 'T' not in clean_due:
                # Handle space-separated date/time
                dt = datetime.fromisoformat(clean_due.replace(' ', 'T'))
            else:
                dt = datetime.fromisoformat(clean_due)
            
            # If naive, assume it's UTC (as we standardized on that)
            if dt.tzinfo is None:
                if dt < now_utc: is_overdue = 1
            else:
                # Aware comparison
                from datetime import timezone
                if dt < datetime.now(timezone.utc): is_overdue = 1
        except Exception as e:
            print(f"DEBUG: Overdue check failed for {task_id}: {e}")

    return TaskResponse(
        id=task_id,
        title=title,
        due_iso=due_iso or "",
        priority=priority,
        notified=0,
        created_iso=created_iso,
        completed_iso=row.get("updated_at") if is_completed else None,
        category=category,
        description=desc,
        status="completed" if is_completed else "open",
        is_overdue=is_overdue,
    )


def list_tasks_for_session(session: UserSession) -> list[TaskResponse]:
    print(f"DEBUG: Listing tasks for {session.uid}")
    rows = supabase.get_tasks(session.uid)
    return [_row_to_task(session, row) for row in rows]


def create_task_for_session(session: UserSession, payload: TaskCreateRequest) -> TaskResponse:
    print(f"DEBUG: Creating task: {payload.title} for {session.uid}")
    full_text = f"{payload.title}\n{payload.description}"
    ct_b64, nonce_b64 = encrypt_bytes(full_text.encode("utf-8"), session.key)
    encrypted_payload = f"{nonce_b64}:{ct_b64}"

    task_row = {
        "title": payload.title,
        "due_iso": payload.due_iso,
        "priority": payload.priority,
        "category": payload.category,
        "encrypted_data": encrypted_payload,
    }
    
    new_task = supabase.create_task(session.uid, task_row)
    if not new_task:
        print(f"DEBUG ERROR: Failed to create task in Supabase for {session.uid}")
        raise HTTPException(status_code=500, detail="Failed to save task to database. Please check your Supabase connection and policies.")
        
    print(f"DEBUG: Task saved to Supabase with ID: {new_task.get('id')}")
    supabase.log_audit(session.uid, "task_created", f"Created task: {payload.title}")
    return _row_to_task(session, new_task)


def update_task_for_session(
    session: UserSession,
    task_id: str,
    payload: TaskUpdateRequest,
) -> TaskResponse | None:
    print(f"DEBUG: Updating task {task_id} for {session.uid}")
    full_text = f"{payload.title}\n{payload.description}"
    ct_b64, nonce_b64 = encrypt_bytes(full_text.encode("utf-8"), session.key)
    encrypted_payload = f"{nonce_b64}:{ct_b64}"

    updates = {
        "title": payload.title,
        "due_iso": payload.due_iso,
        "priority": payload.priority,
        "category": payload.category,
        "encrypted_data": encrypted_payload,
    }
    
    updated = supabase.update_task(session.uid, task_id, updates)
    if not updated:
        print(f"DEBUG ERROR: Failed to update task {task_id}")
        return None
        
    supabase.log_audit(session.uid, "task_edited", f"Edited task: {payload.title}")
    return _row_to_task(session, updated)


def complete_task_for_session(session: UserSession, task_id: str, completed_iso: str):
    task = _get_task_raw(session.uid, task_id)
    title = task.get("title", "Unknown Task") if task else "Unknown Task"
    supabase.update_task(session.uid, task_id, {"is_completed": True})
    supabase.log_audit(session.uid, "task_completed", f"Completed task: {title}")


def reopen_task_for_session(session: UserSession, task_id: str):
    task = _get_task_raw(session.uid, task_id)
    title = task.get("title", "Unknown Task") if task else "Unknown Task"
    supabase.update_task(session.uid, task_id, {"is_completed": False})
    supabase.log_audit(session.uid, "task_reopened", f"Reopened task: {title}")


def snooze_task_for_session(session: UserSession, task_id: str, minutes: int):
    task = _get_task_raw(session.uid, task_id)
    if not task: return
    
    title = task.get("title", "Unknown Task")
    due_iso = task.get("due_iso")
    
    if due_iso:
        try:
            # Handle ISO format with or without 'T'
            raw_due = due_iso
            if raw_due.endswith('Z'):
                dt = datetime.fromisoformat(raw_due.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(raw_due.replace('Z', ''))
            
            new_dt = dt + timedelta(minutes=minutes)
            
            # If it was UTC, keep it UTC
            if raw_due.endswith('Z'):
                new_iso = new_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                new_iso = new_dt.isoformat()
                
            supabase.update_task(session.uid, task_id, {"due_iso": new_iso})
            supabase.log_audit(session.uid, "task_snoozed", f"Snoozed '{title}' for {minutes}m. New time: {new_iso}")
        except Exception as e:
            print(f"Error parsing date for snooze: {e}")
            supabase.log_audit(session.uid, "task_snoozed", f"Snoozed task '{title}' for {minutes}m")
    else:
        supabase.log_audit(session.uid, "task_snoozed", f"Snoozed task '{title}' for {minutes}m")


def delete_task_for_session(session: UserSession, task_id: str):
    task = _get_task_raw(session.uid, task_id)
    title = task.get("title", "Unknown Task") if task else "Unknown Task"
    supabase.delete_task(session.uid, task_id)
    supabase.log_audit(session.uid, "task_deleted", f"Deleted task: {title}")


def _get_task_raw(user_id: str, task_id: str) -> dict | None:
    try:
        rows = supabase.supabase.table("tasks").select("*").eq("id", task_id).eq("user_id", user_id).execute()
        return rows.data[0] if rows.data else None
    except:
        return None


def delete_all_tasks_for_session(session: UserSession):
    supabase.delete_all_tasks(session.uid)
    supabase.log_audit(session.uid, "all_tasks_cleared", "Cleared all tasks from workspace")


def log_notification_event_for_session(
    session: UserSession,
    task_id: str,
    event: str,
    extra: str = "",
) -> bool:
    # Strip 'notification_' prefix if the client accidentally included it
    clean_event = event.replace("notification_", "") if event.startswith("notification_") else event

    # Update task state in DB
    updates = {"notification_status": clean_event}
    if clean_event == "missed":
        updates["is_overdue"] = 1
    elif clean_event == "triggered" or clean_event == "sent":
        updates["notified"] = 1
        
    try:
        supabase.update_task(session.uid, task_id, updates)
    except:
        pass
    # Attempt to use task title instead of raw id in audit logs for clarity
    task = _get_task_raw(session.uid, task_id)
    task_title = task.get("title") if task else task_id

    # Only log scheduled/triggered notifications when relevant
    details = extra
    if task_title and task_title not in details:
        # Prefer descriptive 'Task: <title>' prefix if title isn't already in details
        details = f"Task: {task_title}" + (f" — {details}" if details else "")

    try:
        supabase.log_audit(session.uid, f"notification_{clean_event}", details)
    except Exception as e:
        print(f"Error logging notification event for {task_id}: {e}")

    return True
