import os
import sys

# Add project root to python path
sys.path.insert(0, r'c:\Users\User\Documents\RemindMe')

from backend.supabase_auth import supabase_admin

try:
    print("Querying 'usernames' table in Supabase...")
    res = supabase_admin.table("usernames").select("*").execute()
    print("SUCCESS!")
    print(f"Data count: {len(res.data) if res.data else 0}")
    print("Data:")
    import json
    print(json.dumps(res.data, indent=2))
except Exception as e:
    print("FAILED to query 'usernames' table:")
    print(e)
