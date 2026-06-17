import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.supabase_auth import supabase, supabase_admin, get_auth_user_by_email, _get_auth_user_by_email_fallback

def run_tests():
    print("=== SUPABASE CLIENT TEST ===")
    
    # 1. Test anon select from usernames table
    print("\n1. Running Select with Anon Client...")
    try:
        res = supabase.table("usernames").select("*").eq("username", "wassim").execute()
        print("Anon Client wassim query success!")
        print("Data:", res.data)
    except Exception as e:
        print("Anon Client query failed:", e)

    # 2. Test admin select from usernames table
    print("\n2. Running Select with Admin Client...")
    try:
        res = supabase_admin.table("usernames").select("*").eq("username", "wassim").execute()
        print("Admin Client wassim query success!")
        print("Data:", res.data)
    except Exception as e:
        print("Admin Client query failed:", e)

    # 3. Test fallback function
    print("\n3. Testing _get_auth_user_by_email_fallback for wassim email...")
    try:
        res, err = _get_auth_user_by_email_fallback("1231302326@student.mmu.edu.my")
        print("Fallback for wassim result:", res)
        print("Fallback for wassim error:", err)
    except Exception as e:
        print("Fallback for wassim failed:", e)

    # 4. Test fallback function for abdelkarim
    print("\n4. Testing _get_auth_user_by_email_fallback for abdelkarim email...")
    try:
        res, err = _get_auth_user_by_email_fallback("svmeftahabdelkrim@gmail.com")
        print("Fallback for abdelkarim result:", res)
        print("Fallback for abdelkarim error:", err)
    except Exception as e:
        print("Fallback for abdelkarim failed:", e)

    # 5. Test get_auth_user_by_email
    print("\n5. Testing get_auth_user_by_email for wassim email...")
    try:
        res, err = get_auth_user_by_email("1231302326@student.mmu.edu.my")
        print("get_auth_user_by_email wassim result:", res)
        print("get_auth_user_by_email wassim error:", err)
    except Exception as e:
        print("get_auth_user_by_email wassim failed:", e)

if __name__ == "__main__":
    run_tests()
