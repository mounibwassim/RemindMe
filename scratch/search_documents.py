import os
import re

paths = [
    os.path.expandvars(r"%USERPROFILE%\Downloads"),
    os.path.expandvars(r"%USERPROFILE%\Desktop"),
    os.path.expandvars(r"%USERPROFILE%\Documents"),
]

pattern = re.compile(rb'[a-zA-Z0-9-]+\.onrender\.com')
found = set()

for path in paths:
    if os.path.exists(path):
        print(f"Searching: {path}")
        for root, dirs, files in os.walk(path):
            # Skip node_modules, .git, venv
            if any(p in root.lower() for p in ['node_modules', '.git', 'venv', '.venv', '.idea', '.vscode', 'pubspec.lock']):
                continue
            for file in files:
                full_path = os.path.join(root, file)
                try:
                    sz = os.path.getsize(full_path)
                    if sz > 5 * 1024 * 1024: # skip files > 5MB
                        continue
                except:
                    continue
                try:
                    with open(full_path, 'rb') as f:
                        content = f.read()
                        matches = pattern.findall(content)
                        for m in matches:
                            domain = m.decode('utf-8', errors='ignore')
                            found.add(domain)
                except Exception as e:
                    pass

print("\n=== Search Results inside Documents/Downloads/Desktop ===")
if found:
    for item in sorted(found):
        print(item)
else:
    print("No matching onrender.com URLs found.")
