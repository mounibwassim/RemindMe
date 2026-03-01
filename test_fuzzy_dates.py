import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.ai_assistant import extract_task_details

test_cases = [
    "Meeting on 15 januare",
    "Gym on 5 fubruar",
    "Party marshh 10",
    "Reminder for 12 dec",
    "Call mom tmr"
]


print("--- Testing Fuzzy Date Parsing ---")
with open("test_results_explicit.txt", "w", encoding="utf-8") as f:
    f.write("--- Testing Fuzzy Date Parsing ---\n")
    for text in test_cases:
        title, dt, has_time, error = extract_task_details(text)
        log = f"Input: '{text}'"
        print(log)
        f.write(log + "\n")
        if dt:
            log1 = f"  -> Title: {title}"
            log2 = f"  -> Date:  {dt.strftime('%Y-%m-%d')}"
            print(log1)
            f.write(log1 + "\n")
            print(log2)
            f.write(log2 + "\n")
        else:
            log3 = f"  -> Failed: {error}"
            print(log3)
            f.write(log3 + "\n")
        print("-" * 30)
        f.write("-" * 30 + "\n")
