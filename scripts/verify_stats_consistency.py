from backend.stats_service import get_task_counts_formula, get_weekly_completion_distribution
import os
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "tasks_test_verify.db"

def setup_test_db():
    if os.path.exists(DB_PATH): os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE tasks (
        id INTEGER PRIMARY KEY, status TEXT, completed_iso TEXT, due_iso TEXT, created_iso TEXT, priority INTEGER
    )""")
    
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    
    # 1. Completed Today
    cur.execute("INSERT INTO tasks (status, completed_iso, due_iso, created_iso, priority) VALUES (?, ?, ?, ?, ?)",
                ("completed", f"{today_str}T10:00:00", f"{today_str}T09:00:00", f"{today_str}T08:00:00", 3))
    
    # 2. Pending (Overdue)
    past_due = (now - timedelta(hours=1)).isoformat()
    cur.execute("INSERT INTO tasks (status, completed_iso, due_iso, created_iso, priority) VALUES (?, ?, ?, ?, ?)",
                ("open", None, past_due, today_str, 1))
                
    # 3. Upcoming
    future_due = (now + timedelta(hours=5)).isoformat()
    cur.execute("INSERT INTO tasks (status, completed_iso, due_iso, created_iso, priority) VALUES (?, ?, ?, ?, ?)",
                ("open", None, future_due, today_str, 2))
                
    conn.commit()
    conn.close()

def verify():
    setup_test_db()
    
    comp, pend, upc, total = get_task_counts_formula(DB_PATH)    # Verification
    print(f"Stats: Comp={comp}, Pend={pend}, Upc={upc}, Total={total}")
    assert comp == 1, f"Expected 1 completed, got {comp}"
    assert pend == 1, f"Expected 1 pending, got {pend}"
    assert upc == 1, f"Expected 1 upcoming, got {upc}"
    assert total == 3, f"Expected 3 total tasks, got {total}"
    print("[SUCCESS] Formula Check Passed: Total = Comp + Pend + Upc")

    # The original code used DB_PATH, but the instruction's Code Edit uses temp_db.
    # Assuming temp_db is meant to be DB_PATH based on context.
    dist = get_weekly_completion_distribution(DB_PATH, 0) 
    print(f"Weekly Dist Counts: {dist['counts']}")
    # The original code used today_idx, but the instruction's Code Edit uses 1 (Tuesday).
    # Assuming the instruction wants to fix the test to a specific day or expects a specific setup.
    # For consistency with the provided Code Edit, using index 1.
    assert dist['counts'][1] == 1, "Tuesday should have 1 completed task"
    print("[SUCCESS] Weekly Distribution Check Passed (Tuesday is correct)")

    print("\n--- ALL STATS CONSISTENCY CHECKS PASSED ---")
    
    os.remove(DB_PATH)

if __name__ == "__main__":
    verify()
