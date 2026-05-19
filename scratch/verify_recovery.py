import os
import traceback
from supabase import create_client, Client
from dotenv import load_dotenv

# Load env from the standard location
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend_api", ".env")
load_dotenv(env_path)

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def test_recovery(email, redirect_url=None):
    print(f"\n--- Testing Recovery for: {email} ---")
    print(f"Redirect URL: {redirect_url}")
    try:
        options = {}
        if redirect_url:
            options["redirect_to"] = redirect_url
            
        print("Calling supabase.auth.reset_password_for_email...")
        response = supabase.auth.reset_password_for_email(email, options=options)
        print(f"SUCCESS: {response}")
    except Exception as e:
        print(f"FAILURE: {type(e).__name__}")
        print(f"Message: {str(e)}")
        # Check for common Supabase error attributes
        if hasattr(e, 'status'): print(f"Status Code: {e.status}")
        if hasattr(e, 'code'): print(f"Error Code: {e.code}")
        traceback.print_exc()

if __name__ == "__main__":
    test_email = "mounibwassimm@gmail.com"
    
    # Test 1: No redirect (Default)
    test_recovery(test_email)
    
    # Test 2: Localhost redirect
    test_recovery(test_email, "http://localhost:3000/reset-password")
    
    # Test 3: Mobile Deep Link
    test_recovery(test_email, "remidme://reset-password")
