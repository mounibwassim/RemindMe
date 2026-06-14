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
        
    with open(LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        
    pattern = rf"DEVELOPER ALERT: OTP for {re.escape(email)} is: (\d{{6}})"
    for line in reversed(lines):
        match = re.search(pattern, line)
        if match:
            return match.group(1)
            
    return None

def test_flow():
    print("=== STARTING CUSTOM OTP ENDPOINTS E2E TEST ===")
    
    # Generate unique test user
    timestamp = int(time.time())
    username = f"testcustom_{timestamp}"
    email = f"testcustom_{timestamp}@gmail.com"
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
    
    time.sleep(1)
    
    print("\n2. Initiating custom forgot-password request...")
    forgot_url = f"{BASE_URL}/api/v1/auth/forgot-password"
    forgot_payload = {
        "username": username
    }
    
    r = requests.post(forgot_url, json=forgot_payload)
    if r.status_code != 200:
        print(f"Forgot password request failed: {r.status_code} - {r.text}")
        sys.exit(1)
    print("Forgot password request successful!")
    
    time.sleep(2)
    
    print("\n3. Extracting OTP from backend_errors.log...")
    otp = get_latest_otp(email)
    if not otp:
        print("ERROR: Could not find the generated OTP in the logs!")
        sys.exit(1)
    print(f"Found OTP code: {otp}")
    
    print("\n4. Verifying OTP via /verify-otp...")
    verify_url = f"{BASE_URL}/api/v1/auth/verify-otp"
    verify_payload = {
        "email": email,
        "otp_code": otp
    }
    
    r = requests.post(verify_url, json=verify_payload)
    if r.status_code != 200:
        print(f"OTP verification failed: {r.status_code} - {r.text}")
        sys.exit(1)
    
    res_data = r.json()
    reset_token = res_data.get("reset_token")
    if not reset_token:
        print("ERROR: verify-otp response did not contain reset_token!")
        sys.exit(1)
    print(f"OTP verification successful! Received reset_token: {reset_token[:30]}...")
    
    print("\n5. Resetting password via /reset-password...")
    reset_url = f"{BASE_URL}/api/v1/auth/reset-password"
    reset_payload = {
        "reset_token": reset_token,
        "new_password": new_password
    }
    
    r = requests.post(reset_url, json=reset_payload)
    if r.status_code != 200:
        print(f"Password reset failed: {r.status_code} - {r.text}")
        sys.exit(1)
    print("Password reset successful!")
    
    print("\n6. Verifying login with the NEW password...")
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
    
    print("\n7. Verifying login with the OLD password should fail...")
    signin_payload_old = {
        "username": username,
        "password": initial_password
    }
    r = requests.post(signin_url, json=signin_payload_old)
    if r.status_code == 200:
        print("ERROR: Login with old password succeeded! Password was not updated.")
        sys.exit(1)
    print("Success: Login with old password failed as expected.")
    
    print("\n=== ALL CUSTOM OTP ENDPOINTS TEST CASES PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_flow()
