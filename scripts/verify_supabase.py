import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Path to .env
env_path = os.path.join(os.getcwd(), "backend_api", ".env")
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(os.getcwd()), "backend_api", ".env")

print(f"Loading .env from: {env_path}")
load_dotenv(env_path)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

print(f"URL: {url}")
print(f"Key starts with: {key[:20]}...")

try:
    supabase: Client = create_client(url, key)
    # Try to get the current role from the database
    res = supabase.rpc("get_my_role").execute()
    print(f"Role from RPC: {res.data}")
except Exception as e:
    print(f"Error checking role: {e}")
    # Fallback: just try to list tasks
    try:
        res = supabase.table("tasks").select("id", count="exact").limit(1).execute()
        print(f"Successfully connected to 'tasks' table. Found {res.count} tasks.")
    except Exception as e2:
        print(f"Error connecting to 'tasks' table: {e2}")

print("\n--- Diagnostic Finish ---")
