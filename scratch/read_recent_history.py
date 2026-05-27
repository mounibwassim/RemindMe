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
        
        # Get the most recently visited 200 URLs
        cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 200")
        rows = cursor.fetchall()
        
        print("\n=== Recent 200 Chrome URLs ===")
        for url, title, visits, last_time in rows:
            print(f"URL: {url} | Title: {title}")
            
        conn.close()
        os.remove(temp_copy)
    except Exception as e:
        print(f"Error reading history: {e}")
