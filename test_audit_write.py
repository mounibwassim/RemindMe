import requests
from backend.auth_service import write_audit_cloud

def test_write():
    uid = "test_uid_123"
    action = "MANUAL_TEST"
    title = "Test Task"
    print(f"Attempting to write audit for {uid}...")
    ok, err = write_audit_cloud(uid, action, task_title=title)
    if ok:
        print("Success!")
    else:
        print(f"Failed: {err}")

if __name__ == "__main__":
    test_write()
