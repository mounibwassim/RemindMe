import requests
import time
import sys
import json

HEALTH_URL = "https://remindme-backend-k9mb.onrender.com/health"
FORGOT_URL = "https://remindme-backend-k9mb.onrender.com/api/v1/auth/firebase/forgot-password"
DEBUG_OTP_URL = "https://remindme-backend-k9mb.onrender.com/api/v1/debug/latest-otp/{username}"
TARGET_COMMIT = "f5fad97"

def check_deployment():
    print(f"Polling {HEALTH_URL} to verify deployment of commit prefix '{TARGET_COMMIT}'...")
    start_time = time.time()
    max_wait = 300 
    
    while True:
        try:
            r = requests.get(HEALTH_URL, timeout=10)
            if r.status_code == 200:
                data = r.json()
                current_commit = data.get("git_commit", "unknown")
                print(f"[{int(time.time() - start_time)}s] Render is running commit: '{current_commit}'")
                if current_commit.startswith(TARGET_COMMIT):
                    print("SUCCESS: Newest commit is fully deployed and active on Render!")
                    return True
            else:
                print(f"[{int(time.time() - start_time)}s] Render health returned status code {r.status_code}")
        except Exception as e:
            print(f"[{int(time.time() - start_time)}s] Connection error: {e}")
            
        if time.time() - start_time > max_wait:
            print("TIMEOUT: Render deployment took too long. Proceeding anyway...")
            return False
            
        time.sleep(15)

def verify_flow(username):
    print(f"\n==========================================")
    print(f"TESTING END-TO-END FLOW FOR USER: '{username}'")
    print(f"==========================================")
    
    # 1. Trigger Forgot Password
    print("1. Triggering forgot password POST request...")
    try:
        r = requests.post(FORGOT_URL, json={"username": username}, timeout=30)
        print(f"Response Status: {r.status_code}")
        print(f"Response Body: {json.dumps(r.json(), indent=2)}")
    except Exception as e:
        print(f"Forgot password request failed: {e}")
        return
        
    # 2. Retrieve OTP from Debug Endpoint
    print("\n2. Fetching generated OTP from debug endpoint...")
    url = DEBUG_OTP_URL.format(username=username)
    try:
        r = requests.get(url, timeout=15)
        print(f"Response Status: {r.status_code}")
        print(f"Response Body: {json.dumps(r.json(), indent=2)}")
    except Exception as e:
        print(f"Debug OTP retrieval failed: {e}")

if __name__ == "__main__":
    deployed = check_deployment()
    if deployed:
        verify_flow("wassim")
        verify_flow("abdelkarim")
