import os
import sys
import uuid
import json
from supabase import create_client, Client
from dotenv import load_dotenv

# Setup paths and environment
sys.stdout.reconfigure(encoding='utf-8')
env_path = os.path.join(os.getcwd(), "backend_api", ".env")
load_dotenv(env_path)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Create a test session structure
from app.services.session_store import create_dev_session, get_session_by_id
from app.services.task_service import (
    create_task_for_session,
    complete_task_for_session,
    snooze_task_for_session,
    delete_task_for_session
)
from app.services.analytics_service import reset_analytics_for_session, get_recent_audit_logs
from app.schemas import TaskCreateRequest

username = f"audit_test_{uuid.uuid4().hex[:8]}"
email = f"{username}@test.com"
secret = "testsecretpassword"

print(f"1. Creating test session for: {username}")
session = create_dev_session(username, email, secret)
print(f"Session created with UID: {session.uid}")

try:
    # Verify Audit Log - Add data
    print("\n2. Creating a task (Add data)...")
    task_payload = TaskCreateRequest(
        title="Submit FYP Report",
        due_iso="2026-06-15T10:30:00Z",
        priority=3,
        category="General",
        sound="Default",
        description="Final Year Project report submission"
    )
    task = create_task_for_session(session, task_payload)
    print(f"Task created: '{task.title}' (ID: {task.id})")

    # Verify Audit Log - Complete task
    print(f"\n3. Completing the task: '{task.title}'...")
    complete_task_for_session(session, task.id, "2026-06-15T11:15:00Z")
    print("Task marked completed.")

    # Verify Audit Log - Snooze task
    print(f"\n4. Snoozing the task for 10 minutes...")
    snooze_task_for_session(session, task.id, 10)
    print("Task snoozed.")

    # Verify Audit Log - Delete record
    print(f"\n5. Deleting the task...")
    delete_task_for_session(session, task.id)
    print("Task deleted.")

    # Verify Audit Log - Reset items
    print(f"\n6. Resetting analytics (Reset items)...")
    reset_analytics_for_session(session)
    print("Analytics reset performed.")

    # Fetch logs from DB to verify structure
    print("\n7. Fetching generated audit logs from Supabase...")
    logs = get_recent_audit_logs(session, period="week", limit=50)
    print(f"Total audit logs retrieved: {len(logs)}")
    
    for log in logs:
        print(f"\n- Log ID: {log.id}")
        print(f"  Event: {log.event}")
        print(f"  Details JSON: {log.extra}")
        if log.extra and log.extra.strip().startswith('{'):
            details = json.loads(log.extra)
            print(f"  Parsed Action: {details.get('action_type')}")
            print(f"  Parsed Task/Notes: {details.get('notes')}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n--- Test finished ---")
