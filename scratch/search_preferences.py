import json
import os

pref_path = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Preferences")
print(f"Reading Chrome Preferences: {pref_path}")

if not os.path.exists(pref_path):
    print("Preferences file not found.")
else:
    try:
        with open(pref_path, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
            
        # Serialize back to string to search
        serialized = json.dumps(data)
        
        # Search for onrender.com URLs
        import re
        urls = re.findall(r'https?://[a-zA-Z0-9.-]+\.onrender\.com', serialized)
        print("\n=== Found onrender URLs in Preferences ===")
        for url in set(urls):
            print(url)
            
        # Search for srv-
        srvs = re.findall(r'srv-[a-zA-Z0-9]+', serialized)
        print("\n=== Found srv- IDs in Preferences ===")
        for srv in set(srvs):
            print(srv)
            
    except Exception as e:
        print(f"Error: {e}")
