import requests
import json
from backend.config import FIREBASE_DATABASE_URL

def delete_by_email(target_email):
    base = FIREBASE_DATABASE_URL.rstrip('/')
    url = f"{base}/usernames.json"
    
    print(f"Fetching users from {url}...")
    try:
        r = requests.get(url)
        data = r.json()
        
        if not data:
            print("No users found in database.")
            return

        found = False
        for username, details in data.items():
            if isinstance(details, dict) and details.get('email') == target_email:
                print(f"Found match: {username} -> {target_email}. Deleting...")
                del_url = f"{base}/usernames/{username}.json"
                dr = requests.delete(del_url)
                if dr.status_code == 200:
                    print(f"Successfully deleted {username}")
                    found = True
                else:
                    print(f"Failed to delete {username}: {dr.status_code}")
        
        if not found:
            print(f"No account found for email: {target_email}")
        else:
            print("Deletion process completed.")
            
    except Exception as e:
        print(f"Error during deletion: {e}")

if __name__ == "__main__":
    delete_by_email("1231302326@student.mmu.edu.my")
