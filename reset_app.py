import os
import glob
import shutil

def reset():
    print("🚀 Starting full application data reset...")
    
    # Files to delete
    patterns = [
        "accounts.json",
        "key_salt_*.bin",
        "tasks_*.db",
        "app_debug.log",
        "last_user.txt" # Just in case it exists
    ]
    
    deleted_count = 0
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"✅ Deleted file: {file_path}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    print(f"✅ Deleted directory: {file_path}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ Error deleting {file_path}: {e}")
                
    # Also check in project root if things moved
    print(f"\n✨ Reset complete. {deleted_count} files/folders removed.")
    print("You can now start the app for a fresh registration.")

if __name__ == "__main__":
    reset()
