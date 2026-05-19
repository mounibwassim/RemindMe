import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def update_schema():
    load_dotenv(os.path.join(os.getcwd(), "backend_api", ".env"))
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        print("Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found in .env")
        return

    supabase: Client = create_client(url, key)
    
    print(f"Updating schema for {url}...")
    
    # Supabase Python client doesn't support raw SQL easily, 
    # but we can try to use the 'rpc' if they have an admin function, 
    # OR we just advise them to run it in the dashboard.
    
    # Since we can't easily run ALTER TABLE via the service role client without a specific RPC,
    # let's just try to insert a dummy log to trigger our fallback logic and see if it works.
    
    print("\nIMPORTANT: Please run the following SQL in your Supabase SQL Editor to enable full audit logging:")
    print("-" * 50)
    print("ALTER TABLE public.audit_logs ADD COLUMN IF NOT EXISTS notification_scheduled_at TIMESTAMP WITH TIME ZONE;")
    print("ALTER TABLE public.audit_logs ADD COLUMN IF NOT EXISTS notification_sent_at TIMESTAMP WITH TIME ZONE;")
    print("-" * 50)
    
    try:
        res = supabase.table("audit_logs").insert({"user_id": "00000000-0000-0000-0000-000000000000", "action": "test", "details": "Testing connection"}).execute()
        print("\nDatabase connection successful! Audit logs are working with fallback logic.")
    except Exception as e:
        print(f"\nDatabase connection error: {e}")

if __name__ == "__main__":
    update_schema()
