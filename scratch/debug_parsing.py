import sys
import os
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.ai_assistant import parse_date_time_smart, extract_task_details

def debug_parse():
    text = "meeting tomorrow at 9 am"
    print(f"Testing: {text}")
    dt, has_time, found = parse_date_time_smart(text)
    print(f"parse_date_time_smart result: {dt}, {has_time}, {found}")
    
    title, dt2, has_time2, error = extract_task_details(text)
    print(f"extract_task_details result: {dt2}, {has_time2}, {error}")

if __name__ == "__main__":
    debug_parse()
