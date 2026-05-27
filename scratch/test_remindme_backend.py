import requests

url = "https://remindme-backend.onrender.com"

endpoints = ["/", "/health", "/docs", "/api/v1/tasks"]
for ep in endpoints:
    full_url = f"{url}{ep}"
    print(f"GET {full_url}")
    try:
        r = requests.get(full_url, timeout=10)
        print(f"  Status Code: {r.status_code}")
        print(f"  Headers: {dict(r.headers)}")
        print(f"  Body (first 200 chars): {r.text[:200]}")
    except Exception as e:
        print(f"  Error: {e}")
    print("-" * 50)
