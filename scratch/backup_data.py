import os
import requests
import json
from supabase import create_client, Client
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend_api", ".env")
load_dotenv(env_path)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

FIREBASE_DATABASE_URL = "https://remindme-mounib-default-rtdb.asia-southeast1.firebasedatabase.app"

def backup():
    print("=== DATA BACKUP INITIATED ===")
    backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scratch", "backups"))
    os.makedirs(backup_dir, exist_ok=True)
    
    # 1. Backup Supabase Users
    print("Backing up Supabase Auth users...")
    try:
        users_res = supabase.auth.admin.list_users()
        users_data = []
        for u in users_res:
            users_data.append({
                "id": u.id,
                "email": u.email,
                "created_at": str(u.created_at) if u.created_at else None,
                "last_sign_in_at": str(u.last_sign_in_at) if u.last_sign_in_at else None
            })
        with open(os.path.join(backup_dir, "supabase_users_backup.json"), "w", encoding="utf-8") as f:
            json.dump(users_data, f, indent=2)
        print("Supabase Auth users backed up successfully.")
    except Exception as e:
        print(f"Failed to backup Supabase users: {e}")
        
    # 2. Backup Firebase RTDB Mappings
    print("Backing up Firebase Realtime Database mappings...")
    try:
        url = f"{FIREBASE_DATABASE_URL}/usernames.json"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            mappings = r.json()
            with open(os.path.join(backup_dir, "firebase_mappings_backup.json"), "w", encoding="utf-8") as f:
                json.dump(mappings, f, indent=2)
            print("Firebase RTDB mappings backed up successfully.")
        else:
            print(f"RTDB request failed: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Failed to backup Firebase mappings: {e}")

    # 3. Backup Supabase Tasks
    print("Backing up Supabase tasks table...")
    try:
        res = supabase.table("tasks").select("*").execute()
        tasks = res.data
        with open(os.path.join(backup_dir, "supabase_tasks_backup.json"), "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2)
        print("Supabase tasks table backed up successfully.")
    except Exception as e:
        print(f"Failed to backup tasks: {e}")

    print("=== DATA BACKUP COMPLETED ===")

if __name__ == "__main__":
    backup()
