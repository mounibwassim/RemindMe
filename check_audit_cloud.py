import requests
import json

# Firebase Config
API_KEY = "AIzaSyBGJFf7gNliaDG5pzkuFYv2K59iwrjHiz0"
PROJECT_ID = "remindme-mounib"
FIRESTORE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"

def list_audit_logs():
    url = f"{FIRESTORE_URL}/audit_logs?pageSize=10&key={API_KEY}"
    print(f"Fetching from: {url}")
    r = requests.get(url)
    data = r.json()
    
    if "documents" not in data:
        print("No documents found in 'audit_logs' collection.")
        print("Full response:", json.dumps(data, indent=2))
        return

    print(f"Found {len(data['documents'])} documents in 'audit_logs':")
    for doc in data['documents']:
        fields = doc.get("fields", {})
        uid = fields.get("user_uid", {}).get("stringValue", "N/A")
        action = fields.get("action", {}).get("stringValue", "N/A")
        title = fields.get("task_title", {}).get("stringValue", "N/A")
        ts = fields.get("timestamp", {}).get("stringValue", "N/A")
        print(f"- UID: {uid} | Action: {action} | Title: {title} | TS: {ts}")

if __name__ == "__main__":
    list_audit_logs()
