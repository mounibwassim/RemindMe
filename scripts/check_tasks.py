import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv('backend_api/.env')

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def check_tasks():
    print("Checking tasks in Supabase...")
    response = supabase.table("tasks").select("*").execute()
    tasks = response.data
    print(f"Found {len(tasks)} tasks total.")
    for t in tasks:
        print(f"ROW: {t}")

if __name__ == "__main__":
    check_tasks()
