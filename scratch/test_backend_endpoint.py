import requests

url = "http://localhost:8000/api/v1/auth/firebase/forgot-password"
payload = {"username": "mounib"}

try:
    print(f"Calling {url}...")
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
