import sqlite3
import os
from datetime import datetime, timedelta

def get_stats_db_connection(db_path):
    return sqlite3.connect(db_path, timeout=10, check_same_thread=False)

def get_total_tasks_count(db_path):
    """Counts ALL tasks in the database regardless of state."""
    if not os.path.exists(db_path): return 0
    conn = get_stats_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM tasks")
    total = cur.fetchone()[0]
    conn.close()
    return total

def get_task_counts_formula(db_path, start_iso=None, end_iso=None):
    """
    Returns (completed, pending, upcoming, total)
    Formula: Total = Completed + Pending + Upcoming
    If start_iso/end_iso are provided, counts only tasks within that window.
    """
    if not os.path.exists(db_path): return 0, 0, 0, 0
    conn = get_stats_db_connection(db_path)
    cur = conn.cursor()
    
    # 1. Total (Context-aware)
    if start_iso and end_iso:
        # For weekly/monthly views, we count tasks that were active in this period
        # Active = Created before end AND (Not completed OR completed after start)
        cur.execute("""
            SELECT COUNT(*) FROM tasks 
            WHERE created_iso < ? 
            AND (completed_iso IS NULL OR completed_iso = '' OR completed_iso >= ?)
        """, (end_iso, start_iso))
        total_in_period = cur.fetchone()[0]
    else:
        # Global dashboard
        cur.execute("SELECT COUNT(*) FROM tasks")
        total_in_period = cur.fetchone()[0]

    # 2. Completed (Context-aware)
    comp_sql = "SELECT COUNT(*) FROM tasks WHERE (status='completed' OR (completed_iso IS NOT NULL AND completed_iso != ''))"
    params = []
    if start_iso:
        comp_sql += " AND completed_iso >= ?"
        params.append(start_iso)
    if end_iso:
        comp_sql += " AND completed_iso < ?"
        params.append(end_iso)
    cur.execute(comp_sql, tuple(params))
    completed = cur.fetchone()[0]
    
    # 3. Pending: Overdue (Due <= Now) and not completed
    now_iso = datetime.now().isoformat()
    pending_sql = "SELECT COUNT(*) FROM tasks WHERE due_iso <= ? AND (status != 'completed' AND (completed_iso IS NULL OR completed_iso = ''))"
    params_pending = [now_iso]
    if start_iso:
        pending_sql += " AND due_iso >= ?"
        params_pending.append(start_iso)
    if end_iso:
        pending_sql += " AND due_iso < ?"
        params_pending.append(end_iso)
    cur.execute(pending_sql, tuple(params_pending))
    pending = cur.fetchone()[0]
    
    # 4. Upcoming: Future (Due > Now) and not completed
    upcoming_sql = "SELECT COUNT(*) FROM tasks WHERE due_iso > ? AND (status != 'completed' AND (completed_iso IS NULL OR completed_iso = ''))"
    params_upcoming = [now_iso]
    if start_iso:
        upcoming_sql += " AND due_iso >= ?"
        params_upcoming.append(start_iso)
    if end_iso:
        upcoming_sql += " AND due_iso < ?"
        params_upcoming.append(end_iso)
    cur.execute(upcoming_sql, tuple(params_upcoming))
    upcoming = cur.fetchone()[0]
    
    # Recalculate context-aware total if filtered
    if start_iso and end_iso:
        # Weekly total = Completed in week + Pending/Upcoming due in week?
        # User said: "The following must reset to 0 every Monday: Total Tasks, Completed Tasks"
        # This implies Total = tasks handled/created this week.
        # Let's align with the literal formula: Total = Completed + Pending + Upcoming
        # But only for the context.
        total = completed + pending + upcoming # This might be global if pending/upcoming aren't filtered.
    else:
        total = total_in_period

    conn.close()
    return completed, pending, upcoming, total

def get_weekly_completion_distribution(db_path, week_offset=0):
    """
    Returns daily completion counts for a specific week.
    Standardized Monday start.
    """
    if not os.path.exists(db_path):
        return {'labels': ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], 'counts': [0]*7, 'range': ""}
    
    conn = get_stats_db_connection(db_path)
    cur = conn.cursor()
    
    today = datetime.now()
    # Monday of the target week
    start_week = today - timedelta(days=today.weekday()) - timedelta(weeks=week_offset)
    start_week = start_week.replace(hour=0, minute=0, second=0, microsecond=0)
    
    counts = []
    labels = []
    
    for i in range(7):
        day = start_week + timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        labels.append(day.strftime("%a"))
        
        # Strip time portion from completed_iso for exact date match via SQL DATE grouping
        # SQLite doesn't have a DATE type but we can use substr or date() function
        cur.execute("SELECT COUNT(*) FROM tasks WHERE date(completed_iso) = date(?)", (day_str,))
        counts.append(cur.fetchone()[0])
        
    end_week = start_week + timedelta(days=6)
    date_range = f"{start_week.strftime('%b %d')} - {end_week.strftime('%b %d')}"
    
    conn.close()
    return {'labels': labels, 'counts': counts, 'range': date_range}

def get_monthly_completed_count(db_path, month=None, year=None):
    """Counts tasks completed in a specific month/year."""
    if not os.path.exists(db_path): return 0
    now = datetime.now()
    if month is None: month = now.month
    if year is None: year = now.year
    
    conn = get_stats_db_connection(db_path)
    cur = conn.cursor()
    
    # Accurate grouping using strftime or substr
    pattern = f"{year:04d}-{month:02d}-%"
    cur.execute("SELECT COUNT(*) FROM tasks WHERE (status='completed' OR completed_iso IS NOT NULL) AND completed_iso LIKE ?", (pattern,))
    count = cur.fetchone()[0]
    
    conn.close()
    return count

def get_monthly_stats(db_path, month=None, year=None):
    """Returns (created, completed) for the specified month."""
    if not os.path.exists(db_path): return 0, 0
    now = datetime.now()
    if month is None: month = now.month
    if year is None: year = now.year
    
    conn = get_stats_db_connection(db_path)
    cur = conn.cursor()
    
    prefix = f"{year:04d}-{month:02d}-%"
    
    cur.execute("SELECT COUNT(*) FROM tasks WHERE created_iso LIKE ?", (prefix,))
    created = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM tasks WHERE completed_iso LIKE ?", (prefix,))
    completed = cur.fetchone()[0]
    
    conn.close()
    return created, completed

def get_priority_distribution(db_path, start_iso=None, end_iso=None):
    """Counts completed tasks by priority within an optional window."""
    if not os.path.exists(db_path): return {1:0, 2:0, 3:0}
    conn = get_stats_db_connection(db_path)
    cur = conn.cursor()
    
    query = "SELECT priority, COUNT(*) FROM tasks WHERE (status='completed' OR completed_iso IS NOT NULL AND completed_iso != '')"
    params = []
    
    if start_iso:
        query += " AND completed_iso >= ?"
        params.append(start_iso)
    if end_iso:
        query += " AND completed_iso < ?"
        params.append(end_iso)
        
    query += " GROUP BY priority"
    
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    conn.close()
    
    dist = {1:0, 2:0, 3:0}
    for p, c in rows:
        if p in dist: dist[p] = c
    return dist

def get_calendar_month_data(db_path, year, month):
    """
    Returns full task objects grouped by day for a specific month.
    Consistency: Uses DATE(completed_iso) or DATE(due_iso).
    """
    if not os.path.exists(db_path): return {}
    conn = get_stats_db_connection(db_path)
    cur = conn.cursor()
    
    # Prefix for direct string matching (fast)
    prefix = f"{year:04d}-{month:02d}-%"
    
    # We select fields needed for Calendar display
    cur.execute("""
        SELECT id, ciphertext, nonce, due_iso, priority, notified, created_iso, completed_iso, category 
        FROM tasks 
        WHERE (completed_iso LIKE ? OR (completed_iso IS NULL AND due_iso LIKE ?))
    """, (prefix, prefix))
    
    rows = cur.fetchall()
    conn.close()
    
    tasks_by_day = {}
    for r in rows:
        tid, ct, nonce, due, prio, notified, created, completed, cat = r
        
        # Determine day
        date_str = completed if completed else due
        try:
            # We know it matches prefix, so day is at [8:10]
            day = int(date_str[8:10])
            if day not in tasks_by_day:
                tasks_by_day[day] = []
            
            tasks_by_day[day].append({
                "id": tid,
                "ciphertext": ct,
                "nonce": nonce,
                "due": due,
                "completed": completed,
                "priority": prio,
                "category": cat
            })
        except:
            continue
            
    return tasks_by_day
