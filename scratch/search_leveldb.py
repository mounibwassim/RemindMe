import os
import re

paths = [
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Local Storage\leveldb"),
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\IndexedDB"),
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\databases"),
]

pattern = re.compile(rb'[a-zA-Z0-9-]+\.onrender\.com')
found = set()

for path in paths:
    if os.path.exists(path):
        print(f"Searching: {path}")
        for root, dirs, files in os.walk(path):
            for file in files:
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, 'rb') as f:
                        content = f.read()
                        matches = pattern.findall(content)
                        for m in matches:
                            domain = m.decode('utf-8', errors='ignore')
                            if 'remindme' in domain:
                                found.add(domain)
                except Exception as e:
                    pass
    else:
        print(f"Path does not exist: {path}")

print("\n=== Search Results inside LevelDB / IndexedDB ===")
if found:
    for item in sorted(found):
        print(item)
else:
    print("No matching onrender.com URLs found.")
