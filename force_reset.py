import os
import glob
import shutil
import sys

def nuke():
    print("🔥 Starting GUARANTEED Application Reset...")
    
    # Paths to clear
    paths_to_clear = [
        ".", # Current Dir
    ]
    
    # Windows AppData
    if sys.platform == "win32":
        local_appdata = os.environ.get("LOCALAPPDATA")
        appdata = os.environ.get("APPDATA")
        if local_appdata:
            paths_to_clear.append(os.path.join(local_appdata, "RemindMe"))
        if appdata:
            paths_to_clear.append(os.path.join(appdata, "RemindMe"))
            
    patterns = [
        "accounts.json",
        "key_salt_*.bin",
        "tasks_*.db",
        "app_debug.log",
        "last_user.txt",
        "system.json"
    ]
    
    deleted_count = 0
    
    for base_path in paths_to_clear:
        if not os.path.exists(base_path): continue
        
        for pattern in patterns:
            full_pattern = os.path.join(base_path, pattern)
            for file_path in glob.glob(full_pattern):
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f"✅ Deleted file: {file_path}")
                        deleted_count += 1
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        print(f"✅ Deleted directory: {file_path}")
                        deleted_count += 1
                except Exception as e:
                    print(f"⚠️ Error deleting {file_path}: {e}")
                    
    # Also clean __pycache__
    print("\n🧹 Cleaning Python cache...")
    for root, dirs, files in os.walk("."):
        for d in dirs:
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d))
                deleted_count += 1

    print(f"\n✨ System Reset Successful. {deleted_count} items purged.")
    print("The app is now in a 'Zero State'.")

if __name__ == "__main__":
    nuke()
