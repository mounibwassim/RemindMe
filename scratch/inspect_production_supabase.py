import os
from supabase import create_client, Client
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend_api", ".env")
load_dotenv(env_path)

url = os.environ.get("SUPABASE_URL")
# Use service role key to have admin privileges
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def inspect():
    print("=== SUPABASE PRODUCTION DB INSPECTION ===")
    
    # 1. Fetch Supabase Auth users
    print("\n1. Fetching Supabase Auth Users...")
    auth_emails = set()
    auth_users = {}
    try:
        res = supabase.auth.admin.list_users()
        # list_users returns a list of User objects
        users = []
        if hasattr(res, 'users'):
            users = res.users
        elif isinstance(res, list):
            users = res
        elif hasattr(res, 'data'):
            users = res.data
        else:
            users = res
            
        print(f"Found {len(users)} users in Supabase Auth:")
        for u in users:
            print(f"  - Email: '{u.email}' | ID: '{u.id}' | Created: {u.created_at}")
            auth_emails.add(u.email.strip().lower())
            auth_users[u.email.strip().lower()] = u.id
    except Exception as e:
        print(f"Failed to fetch Supabase Auth users: {e}")

    # 2. Fetch public.usernames table mappings
    print("\n2. Fetching public.usernames mappings...")
    try:
        res = supabase.table("usernames").select("*").execute()
        mappings = res.data
        print(f"Found {len(mappings)} mappings in public.usernames:")
        for m in mappings:
            username = m.get("username")
            email = m.get("email", "").strip().lower()
            uid = m.get("uid")
            print(f"  - Username: '{username}' -> Email: '{email}' | Mapping UID: '{uid}'")
            
            # Check if this mapping email exists in Auth
            if email in auth_emails:
                auth_id = auth_users[email]
                if auth_id != uid:
                    print(f"    WARNING: UID mismatch! Mapping UID is '{uid}', but Auth UID is '{auth_id}'")
            else:
                print(f"    ORPHANED MAPPING: Email '{email}' is NOT registered in Supabase Auth!")
    except Exception as e:
        print(f"Failed to fetch public.usernames mappings: {e}")

if __name__ == "__main__":
    inspect()
