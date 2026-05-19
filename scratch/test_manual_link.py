import os
from supabase import create_client, Client
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend_api", ".env")
load_dotenv(env_path)

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY") # This MUST be the service_role key
supabase: Client = create_client(url, key)

def test_manual_link(email):
    print(f"Generating manual recovery link for: {email}")
    try:
        # We use admin API to bypass SMTP for testing
        res = supabase.auth.admin.generate_link({
            "type": "recovery",
            "email": email,
            "options": {"redirect_to": "http://localhost:3000/reset-password"}
        })
        print(f"SUCCESS! Link: {res.properties.action_link}")
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    test_manual_link("mounibwassimm@gmail.com")
