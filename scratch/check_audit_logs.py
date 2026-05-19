import os
from supabase import create_client

url = "https://nwfyvcfxktggybufsggi.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im53Znl2Y2Z4a3RnZ3lidWZzZ2dpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3ODc1MTc2MSwiZXhwIjoyMDk0MzI3NzYxfQ.4BhIRWJDqCuSFFbHLc0L2q-1YTmxIC52z6zjOg3fAwA"
supabase = create_client(url, key)

try:
    res = supabase.table("audit_logs").select("*").eq("action", "password_reset_failed").order("created_at", desc=True).limit(5).execute()
    print("Recent Password Reset Failures in Audit Logs:")
    for log in res.data:
        print(f"- {log['created_at']}: {log['details']}")
except Exception as e:
    print(f"Error checking audit logs: {e}")
