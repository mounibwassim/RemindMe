import os
import re

cache_path = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache\Cache_Data")
print(f"Searching Chrome Cache at: {cache_path}")

pattern = re.compile(rb'[a-zA-Z0-9-]+\.onrender\.com')

found = set()

if not os.path.exists(cache_path):
    print("Cache path does not exist.")
else:
    for root, dirs, files in os.walk(cache_path):
        for file in files:
            full_path = os.path.join(root, file)
            try:
                sz = os.path.getsize(full_path)
                if sz > 10 * 1024 * 1024: # Skip files > 10MB
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
            except Exception as e:
                pass

print("\n=== Search Results inside Cache ===")
if found:
    for item in sorted(found):
        print(item)
else:
    print("No matching onrender.com URLs found in Chrome Cache.")
