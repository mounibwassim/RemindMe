import requests

candidates = [
    "https://remindme-api.onrender.com",
    "https://remindme-python-api.onrender.com",
    "https://remindme-fastapi.onrender.com",
    "https://remindme-server.onrender.com",
    "https://remindme-app.onrender.com",
    "https://remindme-service.onrender.com",
    "https://remindme-py.onrender.com",
    "https://remindme-prod.onrender.com",
]

for domain in candidates:
    print(f"Testing {domain}...")
    try:
        r = requests.get(f"{domain}/health", timeout=5)
        print(f"  Status: {r.status_code}")
        print(f"  Headers: {dict(r.headers)}")
        print(f"  Body: {r.text[:100]}")
    except Exception as e:
        print(f"  Error: {e}")
    print("-" * 50)
