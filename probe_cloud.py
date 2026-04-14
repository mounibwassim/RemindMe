import requests
import json
import os

def get_config_url():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "config.py")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            for line in f:
                if "FIREBASE_DATABASE_URL" in line and "=" in line:
                    return line.split("=")[1].strip().strip('"').strip("'")
    return None

db_url = get_config_url()
if not db_url:
    print("X Could not find DB URL in config.")
    exit()

print(f"Basing probe on: {db_url}")

# 1. Check root
r = requests.get(f"{db_url}.json?shallow=true")
print(f"Root nodes: {r.json()}")

# 2. Check usernames
r = requests.get(f"{db_url}usernames.json?shallow=true")
print(f"Usernames nodes: {r.json()}")

# 3. Check for 'mounib' specific values
r = requests.get(f"{db_url}usernames/mounib.json")
print(f"Full 'mounib' data: {r.json()}")
