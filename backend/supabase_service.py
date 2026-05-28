import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import List, Optional
import json
import logging

# Configure logging dynamically (resilient to container permissions)
log_file = None
if os.environ.get("APP_ENV") != "production":
    try:
        log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend_errors.log")
        with open(log_file, 'a'):
            pass
    except Exception:
        log_file = None

if log_file:
    logging.basicConfig(
        filename=log_file,
        level=logging.ERROR,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
else:
    logging.basicConfig(
        level=logging.ERROR,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

# Add console handler
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)

logger = logging.getLogger("supabase_service")

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend_api", ".env"))

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
if key:
    is_service = "service_role" in str(key) or "4BhIRWJD" in str(key)
    role_type = "SERVICE_ROLE" if is_service else "ANON"
    print(f"DEBUG: Supabase initialized with {role_type} key (starts with {key[:15]}...)")
else:
    print("DEBUG: SUPABASE_KEY NOT FOUND!")
supabase: Client = create_client(url, key)

def get_tasks(user_id: str) -> List[dict]:
    """Fetch tasks for a user from Supabase."""
    print(f"DEBUG: Fetching tasks for user_id: {user_id}")
    try:
        response = supabase.table("tasks").select("*").eq("user_id", user_id).execute()
        print(f"DEBUG: Fetched {len(response.data)} tasks.")
        return response.data
    except Exception as e:
        print(f"DEBUG ERROR in get_tasks: {e}")
        logger.error(f"Error fetching tasks: {e}")
        return []

def create_task(user_id: str, task_data: dict) -> dict:
    """Create a new task in Supabase."""
    print(f"DEBUG: Creating task for user_id: {user_id}. Data: {task_data}")
    try:
        # Ensure required server-side fields are present.
        # The table uses `is_completed` and `updated_at` to represent completion;
        # we also store the encrypted payload under `encrypted_data`.
        task_data["user_id"] = user_id
        response = supabase.table("tasks").insert(task_data).execute()
        print(f"DEBUG: Task created response data: {response.data}")
        return response.data[0] if response.data else {}
    except Exception as e:
        print(f"DEBUG ERROR in create_task: {e}")
        logger.error(f"Error creating task: {e}")
        return {}

def update_task(user_id: str, task_id: str, updates: dict) -> dict:
    """Update an existing task in Supabase."""
    response = supabase.table("tasks").update(updates).eq("id", task_id).eq("user_id", user_id).execute()
    return response.data[0] if response.data else {}

def delete_task(user_id: str, task_id: str):
    """Delete a task from Supabase."""
    supabase.table("tasks").delete().eq("id", task_id).eq("user_id", user_id).execute()

def log_audit(user_id: str, action: str, details: str, scheduled_at: str = None, sent_at: str = None):
    """Log an audit event to Supabase."""
    print(f"DEBUG: Logging audit: {action} for {user_id}")
    try:
        payload = {
            "user_id": user_id,
            "action": action,
            "details": details
        }
        if scheduled_at: payload["notification_scheduled_at"] = scheduled_at
        if sent_at: payload["notification_sent_at"] = sent_at
        
        try:
            supabase.table("audit_logs").insert(payload).execute()
        except Exception as e:
            if "column" in str(e).lower():
                print(f"DEBUG WARNING: Missing columns in audit_logs, retrying with basic info. Error: {e}")
                # Fallback to basic columns if new ones haven't been added to DB yet
                basic_payload = {
                    "user_id": user_id,
                    "action": action,
                    "details": details
                }
                supabase.table("audit_logs").insert(basic_payload).execute()
            else:
                raise e
    except Exception as e:
        print(f"DEBUG ERROR in log_audit: {e}")
        logger.error(f"Error logging audit: {e}")

def get_audit_logs(user_id: str, limit: int = 50) -> List[dict]:
    """Fetch audit logs from Supabase."""
    response = supabase.table("audit_logs").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
    return response.data

def update_analytics(user_id: str, stats: dict):
    """Update analytics for a user in Supabase."""
    supabase.table("analytics").upsert({
        "user_id": user_id,
        "stats_json": stats,
        "last_updated": "now()"
    }, on_conflict="user_id").execute()

def delete_all_tasks(user_id: str):
    """Clear all tasks for a user."""
    supabase.table("tasks").delete().eq("user_id", user_id).execute()


def delete_analytics(user_id: str):
    """Delete analytics row for a user."""
    try:
        supabase.table("analytics").delete().eq("user_id", user_id).execute()
    except Exception as e:
        print(f"DEBUG ERROR in delete_analytics: {e}")
        logger.error(f"Error deleting analytics for {user_id}: {e}")
