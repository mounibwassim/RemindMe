import sys
import os
from datetime import datetime, timedelta

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.ai_assistant import extract_task_details

def test_extract():
    test_cases = [
        "next Friday at 3 pm",
        "buy milk next Friday at 3 pm",
        "meeting tomorrow at 9 am",
        "gym at 5pm",
    ]
    
    print(f"Current time: {datetime.now()}")
    for tc in test_cases:
        title, dt, has_time, error = extract_task_details(tc)
        print(f"Input: {tc}")
        print(f"  Title: {title}")
        print(f"  DateTime: {dt}")
        print(f"  Has Time: {has_time}")
        print(f"  Error: {error}")
        print("-" * 20)

if __name__ == "__main__":
    test_extract()
