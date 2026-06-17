import requests
import json

URL = "https://remindme-backend-k9mb.onrender.com/api/v1/auth/firebase/forgot-password"

def test_endpoint(username):
    print(f"Testing POST {URL} for username '{username}'...")
    try:
        r = requests.post(URL, json={"username": username}, timeout=20)
        print(f"Status Code: {r.status_code}")
        print(f"Response Headers: {dict(r.headers)}")
        try:
            print(f"Response Body: {json.dumps(r.json(), indent=2)}")
        except Exception:
            print(f"Response Body: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_endpoint("wassim")
