import os
import re

chrome_profile_path = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Profile 2")
print(f"Searching Chrome Profile 2 at: {chrome_profile_path}")

# Regex to find remindme-backend-XXXX.onrender.com or similar
pattern = re.compile(rb'remindme-backend-[a-zA-Z0-9-]{4,12}\.onrender\.com')
pattern2 = re.compile(rb'remindme-[a-zA-Z0-9-]{4,12}\.onrender\.com')
pattern3 = re.compile(rb'srv-d860[a-z0-9]+') # Render service ID

found = set()

# Files/extensions to skip to avoid binary dumps of giant files (like Cache)
skip_files = {
    "History-journal", "Web Data-journal", "Favicons-journal", "History Provider Cache"
}
skip_extensions = {
    ".png", ".jpg", ".jpeg", ".ico", ".pak", ".exe", ".dll", ".zip", ".tar", ".gz"
}

if not os.path.exists(chrome_profile_path):
    print("Profile 2 does not exist.")
else:
    for root, dirs, files in os.walk(chrome_profile_path):
        for file in files:
            if file in skip_files:
                continue
            ext = os.path.splitext(file)[1].lower()
            if ext in skip_extensions:
                continue
                
            full_path = os.path.join(root, file)
            
            try:
                sz = os.path.getsize(full_path)
                if sz > 50 * 1024 * 1024:
                    continue
            except:
                continue
                
            try:
                with open(full_path, 'rb') as f:
                    content = f.read()
                    
                    # Check for matches
                    matches = pattern.findall(content)
                    for m in matches:
                        found.add(m.decode('utf-8', errors='ignore'))
                        
                    matches2 = pattern2.findall(content)
                    for m in matches2:
                        found.add(m.decode('utf-8', errors='ignore'))
                        
                    if b'srv-d860imv7f7vs73e6jsn0' in content:
                        print(f"Found service ID srv-d860imv7f7vs73e6jsn0 in: {full_path}")
                        context_pattern = re.compile(rb'[a-zA-Z0-9.-]+\.onrender\.com')
                        m_ctx = context_pattern.findall(content)
                        for m in m_ctx:
                            found.add(m.decode('utf-8', errors='ignore'))
                            
            except Exception as e:
                pass

print("\n=== Search Results ===")
if found:
    for item in sorted(found):
        print(item)
else:
    print("No matching onrender.com URLs found in Profile 2.")
