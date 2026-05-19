import os
from supabase import create_client

url = "https://nwfyvcfxktggybufsggi.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im53Znl2Y2Z4a3RnZ3lidWZzZ2dpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3ODc1MTc2MSwiZXhwIjoyMDk0MzI3NzYxfQ.4BhIRWJDqCuSFFbHLc0L2q-1YTmxIC52z6zjOg3fAwA"
supabase = create_client(url, key)

try:
    users = supabase.auth.admin.list_users()
    print("Supabase Users:")
    for user in users:
        print(f"- {user.email} (ID: {user.id})")
except Exception as e:
    print(f"Error listing users: {e}")
