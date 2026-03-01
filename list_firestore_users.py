import requests
import json

PROJECT_ID = "remindme-mounib"
FIRESTORE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/users"

def list_users():
    try:
        r = requests.get(FIRESTORE_URL)
        data = r.json()
        if "documents" in data:
            print(f"Found {len(data['documents'])} users in Firestore:")
            for doc in data["documents"]:
                fields = doc.get("fields", {})
                username = fields.get("username", {}).get("stringValue", "N/A")
                email = fields.get("email", {}).get("stringValue", "N/A")
                print(f" - Username: {username}, Email: {email}")
        else:
            print("No users found in collection 'users'.")
            print("Full Response:", json.dumps(data, indent=2))
    except Exception as e:
        print("Error listing users:", e)

if __name__ == "__main__":
    list_users()
