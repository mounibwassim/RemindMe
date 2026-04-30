import sys
import os
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.ai_assistant import parse_date_time_smart

def debug():
    text = "gym at 5pm"
    now = datetime.now()
    print(f"Now: {now}")
    dt, has_time, found = parse_date_time_smart(text)
    print(f"Result: {dt}, {has_time}, {found}")

if __name__ == "__main__":
    debug()
