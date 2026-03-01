import requests
import json
from backend.config import FIREBASE_WEB_API_KEY

PROJECT_ID = "remindme-mounib"
FIRESTORE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"

def check_users():
    url = f"{FIRESTORE_URL}/users?key={FIREBASE_WEB_API_KEY}"
    print(f"Checking users at: {url}")
    r = requests.get(url)
    data = r.json()
    
    if "documents" not in data:
        print("No users found in Firestore.")
        return

    print(f"Found {len(data['documents'])} users:")
    for doc in data['documents']:
        fields = doc.get("fields", {})
        username = fields.get("username", {}).get("stringValue", "N/A")
        email = fields.get("email", {}).get("stringValue", "N/A")
        print(f"- Username: {username} | Email: {email}")

if __name__ == "__main__":
    check_users()
