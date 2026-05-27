import requests

domains = [
    "https://remindme-backend.onrender.com",
    "https://remindme-backend-k9mb.onrender.com",
    "https://api-remindme.onrender.com"
]

for domain in domains:
    print(f"Testing {domain}...")
    try:
        r = requests.get(f"{domain}/health", timeout=10)
        print(f"  /health Status: {r.status_code}")
        print(f"  /health Body: {r.text}")
    except Exception as e:
        print(f"  /health Error: {e}")
        
    try:
        r = requests.get(f"{domain}/docs", timeout=10)
        print(f"  /docs Status: {r.status_code}")
    except Exception as e:
        print(f"  /docs Error: {e}")
    print("-" * 50)
