import requests
import json
import time
import re
import os
import sys

BASE_URL = "http://127.0.0.1:8000"
LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend_errors.log"))

def get_latest_otp(email):
    print(f"Reading logs from {LOG_PATH} to extract OTP for {email}...")
    if not os.path.exists(LOG_PATH):
        print(f"ERROR: Log file not found at {LOG_PATH}")
        return None
        
    # Read the last 50 lines of the log file
    with open(LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        
    # Search from the end of the file for the DEVELOPER ALERT OTP
    pattern = rf"DEVELOPER ALERT: OTP for {re.escape(email)} is: (\d{{6}})"
    for line in reversed(lines):
        match = re.search(pattern, line)
        if match:
            return match.group(1)
            
    return None

def test_flow():
    print("=== STARTING PASSWORD RECOVERY E2E TEST ===")
    
    # Generate unique test user
    timestamp = int(time.time())
    username = f"testrec_{timestamp}"
    email = f"testrec_{timestamp}@gmail.com"
    initial_password = "initial_password_123"
    new_password = "new_secure_password_987"
    
    print(f"1. Creating test user: username={username}, email={email}")
    signup_url = f"{BASE_URL}/api/v1/auth/firebase/signup"
    signup_payload = {
        "display_name": username,
        "email": email,
        "password": initial_password
    }
    
    r = requests.post(signup_url, json=signup_payload)
    if r.status_code != 200:
        print(f"Signup failed: {r.status_code} - {r.text}")
        sys.exit(1)
    print("Signup successful!")
    
    # Wait for a moment to let the DB settle
    time.sleep(1)
    
    print("\n2. Initiating forgot-password request...")
    forgot_url = f"{BASE_URL}/api/v1/auth/firebase/forgot-password"
    forgot_payload = {
        "username": username
    }
    
    r = requests.post(forgot_url, json=forgot_payload)
    if r.status_code != 200:
        print(f"Forgot password request failed: {r.status_code} - {r.text}")
        sys.exit(1)
    print("Forgot password request successful!")
    
    # Wait for log output to write
    time.sleep(2)
    
    print("\n3. Extracting OTP from backend_errors.log...")
    otp = get_latest_otp(email)
    if not otp:
        print("ERROR: Could not find the generated OTP in the logs!")
        sys.exit(1)
    print(f"Found OTP code: {otp}")
    
    print("\n4. Confirming password reset using OTP...")
    confirm_url = f"{BASE_URL}/api/v1/auth/firebase/confirm-password-reset"
    confirm_payload = {
        "email": username,
        "reset_code": otp,
        "new_password": new_password
    }
    
    r = requests.post(confirm_url, json=confirm_payload)
    if r.status_code != 200:
        print(f"Password reset confirmation failed: {r.status_code} - {r.text}")
        sys.exit(1)
    print("Password reset confirmation successful!")
    
    print("\n5. Verifying login with the NEW password...")
    signin_url = f"{BASE_URL}/api/v1/auth/firebase/signin"
    signin_payload = {
        "username": username,
        "password": new_password
    }
    
    r = requests.post(signin_url, json=signin_payload)
    if r.status_code != 200:
        print(f"Login with new password failed: {r.status_code} - {r.text}")
        sys.exit(1)
    print("Login with NEW password successful!")
    
    print("\n6. Verifying login with the OLD password should fail...")
    signin_payload_old = {
        "username": username,
        "password": initial_password
    }
    r = requests.post(signin_url, json=signin_payload_old)
    if r.status_code == 200:
        print("ERROR: Login with old password succeeded! Password was not updated.")
        sys.exit(1)
    print("Success: Login with old password failed as expected.")
    
    print("\n=== ALL E2E TEST CASES PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_flow()
