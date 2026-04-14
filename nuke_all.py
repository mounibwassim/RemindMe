import os
import shutil
import requests
import json
import sys

# Load config to get DB URL
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from backend.config import FIREBASE_DATABASE_URL
except ImportError:
    print("Error: Could not load backend.config. Searching for FIREBASE_DATABASE_URL manually...")
    FIREBASE_DATABASE_URL = None

def get_config_url():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "config.py")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            for line in f:
                if "FIREBASE_DATABASE_URL" in line and "=" in line:
                    return line.split("=")[1].strip().strip('"').strip("'")
    return None

db_url = FIREBASE_DATABASE_URL or get_config_url()

def nuke_local():
    print("--- Cleaning Local Storage ---")
    app_data = os.environ.get('APPDATA')
    if not app_data:
        print("APPDATA not found. Skipping local wipe.")
        return
        
    remind_me_dir = os.path.join(app_data, 'RemindMe')
    if os.path.exists(remind_me_dir):
        try:
            shutil.rmtree(remind_me_dir)
            print(f"Deleted local folder: {remind_me_dir}")
        except Exception as e:
            print(f"Failed to delete local folder (it might be in use): {e}")
    else:
        print("Local folder already empty.")

def nuke_cloud():
    print("\n--- Cleaning Cloud Mappings (RTDB) ---")
    if not db_url:
        print("Database URL not found. Skipping cloud wipe.")
        return
        
    # List of targets to try deleting
    targets = ["usernames", "usernames/mounib"] # Attempting bulk and specific
    
    base_url = db_url.rstrip('/')
    for target in targets:
        url = f"{base_url}/{target}.json"
        try:
            # First check if it exists
            check = requests.get(url, timeout=5)
            if check.status_code == 200 and check.json() is not None:
                print(f"Target found: {target}. Sending DELETE...")
                r = requests.delete(url)
                if r.status_code == 200:
                    print(f"Cloud data '{target}' cleared successfully.")
                else:
                    print(f"Cloud wipe for '{target}' failed (Status {r.status_code})")
            else:
                print(f"Target '{target}' not found or already empty.")
        except Exception as e:
            print(f"Cloud wipe exception for '{target}': {e}")

if __name__ == "__main__":
    force = "--force" in sys.argv
    if force:
        confirm = "NUKE"
    else:
        confirm = input("WARNING: This will delete ALL local tasks and cloud account mappings. type 'NUKE' to continue: ")
        
    if confirm == "NUKE":
        nuke_local()
        nuke_cloud()
        print("\nReset complete! You can now register as a new user.")
    else:
        print("Reset cancelled.")
