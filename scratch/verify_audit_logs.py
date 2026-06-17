import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Reconfigure stdout to support UTF-8 printing of emojis
sys.stdout.reconfigure(encoding='utf-8')

env_path = os.path.join(os.getcwd(), "backend_api", ".env")
load_dotenv(env_path)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

try:
    supabase: Client = create_client(url, key)
    res = supabase.table("audit_logs").select("*").order("created_at", desc=True).limit(20).execute()
    print(f"Total retrieved logs: {len(res.data)}")
    for idx, log in enumerate(res.data):
        print(f"\n--- Log #{idx+1} ---")
        print(f"ID: {log.get('id')}")
        print(f"User ID: {log.get('user_id')}")
        print(f"Action: {log.get('action')}")
        print(f"Details: {log.get('details')}")
        print(f"Created At: {log.get('created_at')}")
except Exception as e:
    print(f"Error fetching audit logs: {e}")
