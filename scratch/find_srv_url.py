import os
import re

chrome_default_path = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default")
print(f"Searching Chrome Default for srv-d860imv7f7vs73e6jsn0 context...")

target_bytes = b'srv-d860imv7f7vs73e6jsn0'

found_contexts = []

for root, dirs, files in os.walk(chrome_default_path):
    for file in files:
        full_path = os.path.join(root, file)
        try:
            if os.path.getsize(full_path) > 30 * 1024 * 1024:
                continue
        except:
            continue
            
        try:
            with open(full_path, 'rb') as f:
                content = f.read()
                if target_bytes in content:
                    print(f"\nFound in: {full_path}")
                    # Find any onrender.com subdomains in this file
                    onrender_matches = re.findall(rb'[a-zA-Z0-9.-]+\.onrender\.com', content)
                    for m in onrender_matches:
                        url_str = m.decode('utf-8', errors='ignore')
                        if url_str not in found_contexts:
                            found_contexts.append(url_str)
                            print(f"  Matched onrender domain in same file: {url_str}")
                            
                    # Print 100 bytes around the occurrence
                    idx = content.find(target_bytes)
                    start = max(0, idx - 150)
                    end = min(len(content), idx + 250)
                    snippet = content[start:end]
                    print("  Snippet context:")
                    print(repr(snippet))
        except Exception as e:
            pass

print("\n=== All Found Domains ===")
for d in found_contexts:
    print(d)
