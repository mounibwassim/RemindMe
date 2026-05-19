import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from backend import supabase_service as supabase

def debug_supabase():
    print("=== Supabase Debug ===")
    try:
        # 1. Test connection and get tables (indirectly)
        print("Fetching tasks...")
        # We need a user_id. Let's try to find one if any exists or just use a dummy one to see if it errors.
        # But wait, we can just try to select * from tasks and see what happens.
        response = supabase.supabase.table("tasks").select("count", count="exact").execute()
        print(f"Total tasks in DB: {response.count}")
        
        print("\nFetching audit logs...")
        response_audit = supabase.supabase.table("audit_logs").select("count", count="exact").execute()
        print(f"Total audit logs in DB: {response_audit.count}")

        print("\nFetching analytics...")
        response_analytics = supabase.supabase.table("analytics").select("count", count="exact").execute()
        print(f"Total analytics records in DB: {response_analytics.count}")

    except Exception as e:
        print(f"DEBUG ERROR: {e}")

if __name__ == "__main__":
    debug_supabase()
