import os
import re

appdata_path = os.path.expandvars(r"%APPDATA%")
local_appdata_path = os.path.expandvars(r"%LOCALAPPDATA%")

print(f"Searching Roaming AppData: {appdata_path}")
print(f"Searching Local AppData: {local_appdata_path}")

pattern = re.compile(rb'[a-zA-Z0-9-]+\.onrender\.com')
found = set()

def search_dir(dir_path):
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            # Skip massive directories/files
            if any(p in root.lower() for p in ['temp', 'cache', 'npm', 'pnpm', 'pip', 'virtualbox', 'cypress']):
                continue
            full_path = os.path.join(root, file)
            try:
                if os.path.getsize(full_path) > 10 * 1024 * 1024:
                    continue
            except:
                continue
            try:
                with open(full_path, 'rb') as f:
                    content = f.read()
                    matches = pattern.findall(content)
                    for m in matches:
                        domain = m.decode('utf-8', errors='ignore')
                        if 'remindme' in domain:
                            found.add(domain)
            except:
                pass

search_dir(appdata_path)
search_dir(local_appdata_path)

print("\n=== Search Results inside AppData ===")
if found:
    for item in sorted(found):
        print(item)
else:
    print("No matching onrender.com URLs found in AppData.")
