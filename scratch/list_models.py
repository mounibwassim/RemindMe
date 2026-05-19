import requests

API_KEY = "AIzaSyAu3NRHxVCzwCLK3Yaq8VsYotPLDUx3Sh4"
url = f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}"

try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        models = response.json().get('models', [])
        print("Available models:")
        for m in models:
            print(f"- {m['name']}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception: {e}")
