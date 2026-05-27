import sqlite3
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')

history_path = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\History")
temp_copy = r"c:\Users\User\Documents\RemindMe\scratch\ChromeHistory"

if not os.path.exists(history_path):
    print("Chrome history file not found.")
else:
    try:
        shutil.copy2(history_path, temp_copy)
        conn = sqlite3.connect(temp_copy)
        cursor = conn.cursor()
        
        cursor.execute("SELECT url, title, visit_count FROM urls WHERE url LIKE '%srv-d860imv7f7vs73e6jsn0%'")
        rows = cursor.fetchall()
        
        print("\n=== All srv-d860imv7f7vs73e6jsn0 URLs ===")
        for url, title, visits in rows:
            print(f"URL: {url} | Visits: {visits} | Title: {title}")
            
        conn.close()
        os.remove(temp_copy)
    except Exception as e:
        print(f"Error: {e}")
