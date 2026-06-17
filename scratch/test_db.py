import os
import sys

# Add root folder to PYTHONPATH
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)

from backend import supabase_service as supabase

user_uid = "115ae207-f59c-47f1-a299-d9aa865a5e9b"  # mounib's UID from active_sessions.json

print("--- Supabase Database Diagnostics (Delete All) ---")
print("Supabase URL:", supabase.url)

try:
    # Test creating multiple tasks
    print("\nCreating 3 test tasks...")
    for i in range(3):
        t = supabase.create_task(user_uid, {
            "title": f"Test Clear Task {i+1}",
            "due_iso": "2026-06-16T12:00:00Z",
            "priority": 3,
            "category": "Gym"
        })
        print(f"Created task {i+1}: ID={t.get('id') if t else None}")

    # Fetch tasks
    tasks = supabase.get_tasks(user_uid)
    print("\nTotal tasks before delete_all:", len(tasks))

    # Test delete_all_tasks
    print("\nCalling delete_all_tasks...")
    supabase.delete_all_tasks(user_uid)
    print("delete_all_tasks completed.")

    # Fetch tasks again
    tasks = supabase.get_tasks(user_uid)
    print("Total tasks after delete_all:", len(tasks))
    if len(tasks) == 0:
        print("SUCCESS: Database is now completely empty.")
    else:
        print("WARNING: Database is not empty. Tasks remaining:", len(tasks))

except Exception as e:
    print("Exception occurred during diagnostics:", e)
