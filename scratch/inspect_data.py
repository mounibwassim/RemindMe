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

def inspect():
    print("=== DATA INSPECTION ===")
    
    # 1. Fetch Supabase users
    print("\nFetching Supabase Auth users...")
    try:
        users_res = supabase.auth.admin.list_users()
        print(f"Found {len(users_res)} users in Supabase Auth:")
        for u in users_res:
            print(f"  - Email: {u.email} | Supabase UUID: {u.id} | Created: {u.created_at}")
    except Exception as e:
        print(f"Failed to fetch Supabase users: {e}")
        
    # 2. Fetch Firebase RTDB mappings
    print("\nFetching Firebase Realtime Database mappings...")
    try:
        url = f"{FIREBASE_DATABASE_URL}/usernames.json"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            mappings = r.json()
            if mappings:
                print(f"Found {len(mappings)} mappings in Firebase RTDB:")
                for username, data in mappings.items():
                    print(f"  - Username: {username} | Email: {data.get('email')} | Firebase UID: {data.get('uid')} | Metadata: {data.get('metadata')}")
            else:
                print("No mappings found.")
        else:
            print(f"RTDB request failed: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Failed to fetch Firebase mappings: {e}")

    # 3. Fetch all tasks in Supabase
    print("\nFetching tasks from Supabase PostgreSQL table...")
    try:
        res = supabase.table("tasks").select("*").execute()
        tasks = res.data
        print(f"Found {len(tasks)} tasks in database:")
        for t in tasks:
            print(f"  - Task ID: {t.get('id')} | User ID: {t.get('user_id')} | Title: {t.get('title')} | Completed: {t.get('is_completed')}")
    except Exception as e:
        print(f"Failed to fetch tasks: {e}")

if __name__ == "__main__":
    inspect()
