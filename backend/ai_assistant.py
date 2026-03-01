import re
from datetime import datetime, timedelta

def correct_typos(text: str) -> str:
    """
    Correct common date/time typos using simple replacement.
    """
    corrections = {
        r"\btmr\b": "tomorrow",
        r"\btmrw\b": "tomorrow",
        r"\btommm?orr?ow\b": "tomorrow", 
        r"\byest\b": "yesterday",
        r"\byest[ae]rday\b": "yesterday", 
        r"\bmin(?:ute)?s?\b": "minutes",
        r"\bhrs?\b": "hours",
        # Month Typos
        r"\bjanu(?:are?|ary?)\b": "january",
        r"\bfub?ru(?:ar?|ary?)\b": "february",
        r"\bmarsh{1,2}\b": "march",
        r"\bqpril\b": "april",
        r"\bmai\b": "may",
        r"\bjune?\b": "june",
        r"\bjuli?\b": "july",
        r"\baug(?:ust)?\b": "august",
        r"\bsep(?:t?ember)?\b": "september",
        r"\boct(?:ober)?\b": "october",
        r"\bnov(?:ember)?\b": "november",
        r"\bdec(?:ember)?\b": "december",
    }
    
    for pattern, replacement in corrections.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text

def is_task_related(text: str) -> bool:
    """
    Strict intent classifier that rejects any input not related to task management.
    """
    text_lower = text.lower()
    
    # Mathematical expression blocker
    if re.search(r'[\+\-\*\/=]\s*\d+', text_lower) and not any(w in text_lower for w in ["buy", "shop", "get", "task", "add", "create"]):
        return False
        
    keyword_whitelist = [
        "create", "schedule", "reminder", "meeting", "tomorrow", "today", "at",
        "task", "remind", "buy", "submit", "shopping", "groceries",
        "study", "school", "class", "exam", "assignment", "book",
        "gym", "sport", "workout", "run", "shop", "mall", "market", "store",
        "meet", "work", "office", "client", "call", "email",
        "doctor", "hospital", "med", "health",
        "flight", "trip", "travel", "vacation",
        "party", "friend", "personal", "family", "home",
        "am", "pm", "morning", "evening", "night", "hour", "minute"
    ]
    
    # Must contain at least one task-oriented semantic keyword
    return any(word in text_lower for word in keyword_whitelist)

def detect_intent(text: str) -> str:
    """
    Detects if the input is a GREETING, UNRELATED question, or a TASK content.
    """
    text = text.strip()
    text_lower = text.lower()
    
    # 1. Greetings (Strict)
    greetings = ["hi", "hello", "hey", "how are you", "good morning", "good evening", "greetings"]
    pattern = r"^(" + "|".join(re.escape(g) for g in greetings) + r")\b"
    
    if re.search(pattern, text_lower):
        if len(text) < 30 and "task" not in text_lower:
            return "GREETING"

    # 2. Strict Domain Restriction Guard
    if not is_task_related(text):
        return "UNRELATED"

    # 3. Block Questions / Chatbot queries
    question_starts = [
        "what", "who", "explain", "solve", "how", "tell me", "give me", 
        "help me", "where", "i need advice", "is it", "are we", "can you",
        "current time", "date", "time", "why", "when", "calculate", "do you",
        "does", "which"
    ]
    if any(text_lower.startswith(k) for k in question_starts):
        return "UNRELATED"
        
    if "how much" in text_lower:
        return "UNRELATED"
        
    if text_lower.endswith("?"):
        if text_lower.startswith("am i") or text_lower.startswith("do i"):
             return "UNRELATED"

    # 4. Non-Action Statements
    non_action_starts = ["i am bored", "i feel", "it is", "today is", "the weather", "i am happy", "i am sad"]
    if any(text_lower.startswith(k) for k in non_action_starts):
         return "UNRELATED"

    return "TASK"

def infer_category(text: str):
    """
    Infer category and icon from title text.
    """
    text_lower = text.lower()
    category = "General"
    icon = "star"
    
    keywords = {
        "study": ("Study", "school"),
        "school": ("Study", "school"),
        "class": ("Study", "school"),
        "exam": ("Study", "school"),
        "assignment": ("Study", "school"),
        "book": ("Study", "book-open-variant"),
        "gym": ("Gym", "dumbbell"),
        "sport": ("Gym", "dumbbell"),
        "workout": ("Gym", "dumbbell"),
        "run": ("Gym", "run"),
        "buy": ("Shopping", "cart"),
        "groceries": ("Shopping", "cart"),
        "shop": ("Shopping", "cart"),
        "mall": ("Shopping", "shopping"),
        "market": ("Shopping", "cart"),
        "store": ("Shopping", "cart"),
        "meet": ("Work", "briefcase"),
        "work": ("Work", "briefcase"),
        "office": ("Work", "briefcase"),
        "client": ("Work", "briefcase"),
        "call": ("Work", "phone"),
        "email": ("Work", "email"),
        "doctor": ("Health", "heart-pulse"),
        "hospital": ("Health", "heart-pulse"),
        "med": ("Health", "pill"),
        "health": ("Health", "heart"),
        "flight": ("Travel", "airplane"),
        "trip": ("Travel", "airplane"),
        "travel": ("Travel", "airplane"),
        "vacation": ("Travel", "airplane"),
        "party": ("Personal", "party-popper"),
        "friend": ("Personal", "account"),
        "personal": ("Personal", "account"),
        "family": ("Personal", "account"),
        "home": ("Personal", "home"),
    }
    
    for k, (cat, ico) in keywords.items():
        if k in text_lower:
            category = cat
            icon = ico
            break
            
    return category, icon

def generate_description(title: str) -> str:
    """
    Deterministic description generator based on keywords.
    """
    title_lower = title.lower()
    if "gym" in title_lower or "workout" in title_lower:
        return "Remember to stay hydrated and track your sets."
    if "study" in title_lower or "exam" in title_lower:
        return "Focus time. Put your phone away and take short breaks."
    if "meet" in title_lower or "call" in title_lower:
        return "Check the agenda and bring necessary notes."
    if "buy" in title_lower or "shop" in title_lower:
        return "Check if you have any coupons or loyalty cards."
    if "doctor" in title_lower or "med" in title_lower:
        return "Bring any relevant medical history or prescriptions."
    return ""

def clean_title_only(text: str) -> str:
    """
    Basic fallback cleaner.
    """
    text = correct_typos(text)
    prefixes = [
        r"i want to\s+", r"i need to\s+", r"remind me to\s+", r"remind me\s+", 
        r"please\s+", r"can you\s+", r"add a task to\s+"
    ]
    for p in prefixes:
        text = re.sub(p, "", text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', text).strip().capitalize()


def parse_date_time_smart(text: str):
    """
    Robustly parses date and time from text using search_dates.
    Returns: (dt_obj, has_time_bool, found_text_list)
    """
    import dateparser
    from dateparser.search import search_dates

    settings = {
        'TIMEZONE': 'local',
        'RETURN_AS_TIMEZONE_AWARE': False
    }
    
    parse_text = correct_typos(text)
    parse_text = re.sub(r'\bafter tomorrow\b', 'day after tomorrow', parse_text, flags=re.IGNORECASE)
    parse_text = re.sub(r'(\d)(pm|am)', r'\1 \2', parse_text, flags=re.IGNORECASE)
    
    # 12 AM explicit mapping to 00:xx to prevent 12:xx PM defaults
    parse_text = re.sub(r'\b12:(\d{2})\s*am\b', r'00:\1', parse_text, flags=re.IGNORECASE)
    parse_text = re.sub(r'\b12\s*am\b', r'00:00', parse_text, flags=re.IGNORECASE)
    
    dt = dateparser.parse(parse_text, settings=settings)
    
    found = search_dates(parse_text, settings=settings)
    final_dt = dt
    found_texts = []
    
    if found:
        valid_found = []
        stopwords = ["to", "me", "go", "a", "the", "for", "in", "on", "at", "of"]
        for text_chunk, d in found:
            if text_chunk.lower() not in stopwords:
                 valid_found.append(d)
                 found_texts.append(text_chunk)
        
        if valid_found and not final_dt:
             final_dt = valid_found[-1]
    
    now = datetime.now()
    if not final_dt:
         return {"status": "incomplete", "missing": "date_or_time"}, False, found_texts

    if final_dt < now:
         if "yesterday" in text.lower():
             return final_dt, False, found_texts
             
         has_digit = bool(re.search(r'\d', text))
         date_keywords = [
             "tomorrow", "day after", "next", "last", "coming",
             "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
             "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"
         ]
         date_mentioned = any(k in text.lower() for k in date_keywords)
         
         if date_mentioned:
             if has_digit:
                 try:
                     next_year_dt = final_dt.replace(year=final_dt.year + 1)
                     if next_year_dt > now:
                         final_dt = next_year_dt
                 except ValueError:
                     pass
             else:
                 try:
                     next_week_dt = final_dt + timedelta(days=7)
                     if next_week_dt > now:
                          final_dt = next_week_dt
                 except:
                     pass
         else:
             # Just time mentioned and it's in the past (e.g. "at 5pm" when it's 6pm)
             # Push to tomorrow
             final_dt = final_dt + timedelta(days=1)

    has_time = bool(re.search(r'\d{1,2}:\d{2}', text) or re.search(r'\d{1,2}\s*(?:am|pm)', text, re.IGNORECASE))
    
    return final_dt, has_time, found_texts

def validate_date(text: str):
    dt, has_time, _ = parse_date_time_smart(text)
    if not dt:
        return None, False, "I couldn't understand that date. Please try 'Tomorrow', 'Monday', or 'Dec 25'."
    now = datetime.now()
    if dt.date() < now.date():
         return None, False, "This is a past date. Please select a future date."
    return dt, True, None

def validate_time(text: str, date_ctx):
    import dateparser
    if isinstance(date_ctx, float):
        date_ctx = datetime.fromtimestamp(date_ctx)
    parse_text = f"{date_ctx.strftime('%Y-%m-%d')} {text}"
    dt = dateparser.parse(parse_text)
    if not dt:
         return None, False, "Invalid time format. Try '5pm', '17:00', or '9:30 am'."
    dt = dt.replace(year=date_ctx.year, month=date_ctx.month, day=date_ctx.day)
    now = datetime.now()
    if dt < now:
        return None, False, "This is a past time. Please select a future time."
    return dt.isoformat(), True, None

def extract_task_details(text: str):
    import dateparser
    clean_title = correct_typos(text)
    
    # 0. Manual Check for "Next/This/Last Weekday"
    # Added abbreviations
    weekdays_map = {
        "monday": 0, "mon": 0, 
        "tuesday": 1, "tue": 1, "tues": 1, 
        "wednesday": 2, "wed": 2, 
        "thursday": 3, "thu": 3, "thur": 3, "thurs": 3,
        "friday": 4, "fri": 4, 
        "saturday": 5, "sat": 5, 
        "sunday": 6, "sun": 6
    }
    
    # Pattern matches "Next Fri", "This Mon", etc.
    wd_pattern = r'\b(next|this|last|coming)\s+(' + '|'.join(weekdays_map.keys()) + r')\b'
    
    manual_dt = None
    manual_found_text = ""
    prefix = ""
    
    match = re.search(wd_pattern, text, re.IGNORECASE)
    if match:
         prefix = match.group(1).lower()
         day_name = match.group(2).lower()
         manual_found_text = match.group(0)
         
         if prefix in ["next", "this", "coming"]:
             target_idx = weekdays_map[day_name]
             now_dt = datetime.now()
             current_idx = now_dt.weekday()
             
             days_ahead = (target_idx - current_idx) % 7
             if days_ahead == 0:
                 days_ahead = 7
                 
             manual_dt = now_dt + timedelta(days=days_ahead)

    # NEW: Check for Explicit "Day Month" (e.g. 4 Jan) if Next Weekday didn't fire
    if not manual_dt:
        months_regex = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"
        # 1. "4 January" or "4th Jan"
        dm_pattern = r'\b(\d{1,2}(?:st|nd|rd|th)?)\s*(?:of)?\s*' + months_regex + r'\b'
        # 2. "January 4" or "Jan 4th"
        md_pattern = r'\b' + months_regex + r'\s+(\d{1,2}(?:st|nd|rd|th)?)\b'
        
        match_dm = re.search(dm_pattern, text, re.IGNORECASE)
        match_md = re.search(md_pattern, text, re.IGNORECASE)
        
        explicit_date_str = ""
        if match_dm:
            explicit_date_str = match_dm.group(0)
        elif match_md:
            explicit_date_str = match_md.group(0)
            
        if explicit_date_str:
             manual_found_text = explicit_date_str
             # Using 'future' ensures "4 Jan" acts as "Upcoming 4 Jan"
             manual_dt = dateparser.parse(explicit_date_str, settings={'TIMEZONE': 'local', 'PREFER_DATES_FROM': 'future'})
             
             # Fallback safety bump if 'future' setting failed to bump (rare but possible)
             if manual_dt:
                 now_chk = datetime.now()
                 if manual_dt.date() < now_chk.date():
                      try:
                          manual_dt = manual_dt.replace(year=manual_dt.year + 1)
                      except: pass
    
    # 1. Standard Parse (finds Time too)
    standard_dt, has_time, found_texts = parse_date_time_smart(text)
    
    final_dt = standard_dt
    
    # 2. Override with Manual logic
    if manual_dt:
        final_dt = manual_dt
        # MERGE TIME from standard_dt if available and not a dictionary
        if has_time and standard_dt and not isinstance(standard_dt, dict):
            final_dt = final_dt.replace(hour=standard_dt.hour, minute=standard_dt.minute, second=0, microsecond=0)
        else:
            final_dt = final_dt.replace(hour=0, minute=0, second=0, microsecond=0)

        # Append found text so it gets stripped
        found_texts.append(manual_found_text)

    # 3. Clean Title
    prefixes = [r"i want to\s+", r"i need to\s+", r"remind me to\s+", r"please\s+", r"create task\s+"]
    for p in prefixes:
        clean_title = re.sub(p, "", clean_title, flags=re.IGNORECASE)
        
    if found_texts:
        found_texts = list(set(found_texts))
        found_texts.sort(key=len, reverse=True)
        for s in found_texts:
             if s:
                 clean_title = re.sub(re.escape(s), "", clean_title, flags=re.IGNORECASE)
                 
    clean_title = re.sub(r'\b(next|on|at|in|by|from)\s*$', '', clean_title, flags=re.IGNORECASE)
    clean_title = re.sub(r'\s+', ' ', clean_title).strip()
    
    if clean_title: 
         clean_title = clean_title[0].upper() + clean_title[1:]

    # Detect if date was EXPLICITLY mentioned
    date_keywords = [
        "tomorrow", "yesterday", "today", "day after", "next", "last", "this", "coming",
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
        "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"
    ]
    date_mentioned = any(k in text.lower() for k in date_keywords) or bool(re.search(r'\d{1,2}/\d{1,2}', text))
    
    if not final_dt or isinstance(final_dt, dict):
        if has_time:
             # Time found but no date -> Default to Today
             final_dt = datetime.now()
             t_dt = dateparser.parse(text, settings={'TIMEZONE': 'local'})
             if t_dt:
                 final_dt = final_dt.replace(hour=t_dt.hour, minute=t_dt.minute, second=0, microsecond=0)
             else:
                 return clean_title, {"status": "incomplete", "missing": "date_or_time"}, False, "missing_date"
        else:
             return clean_title, {"status": "incomplete", "missing": "date_or_time"}, False, "missing_date"
    
    # If time found but NO date mentioned -> Force Today
    now = datetime.now()
    if has_time and not date_mentioned and not manual_dt:
        final_dt = final_dt.replace(year=now.year, month=now.month, day=now.day)

    return clean_title, final_dt, has_time, None

    return clean_title, final_dt, has_time, None

def generate_weekly_insight(db_path, start_dt, completed, created, snoozed, sent):
    """Generates general, non-personal behavioral insights for the 7-day period."""
    import sqlite3
    from datetime import datetime
    
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    
    start_iso = start_dt.isoformat()
    end_iso = datetime.now().isoformat()
    
    # We can still calculate stats to determine WHICH general advice to give,
    # but the text returned must be public/general.
    try:
        cur.execute("SELECT COUNT(*) FROM tasks WHERE due_iso >= ? AND due_iso < ? AND status != 'completed'", (start_iso, end_iso))
        missed = cur.fetchone()[0]
    except:
        missed = 0
        
    try:
        cur.execute("SELECT COUNT(*) FROM tasks WHERE due_iso >= ? AND due_iso < ?", (start_iso, end_iso))
        total_due = cur.fetchone()[0]
    except:
        total_due = missed + completed
        
    missed_rate = int((missed / total_due) * 100) if total_due > 0 else 0
    completion_rate = int((completed / total_due) * 100) if total_due > 0 else 0
    
    try:
        cur.execute("SELECT COUNT(*) FROM tasks WHERE due_iso >= ? AND due_iso < ? AND priority = 1", (start_iso, end_iso))
        high_prio = cur.fetchone()[0]
    except:
        high_prio = 0
        
    conn.close()
    
    high_prio_rate = (high_prio / total_due) * 100 if total_due > 0 else 0
    
    # 6 Scenarios specifically mapped to Advanced Weekly Metrics Requirements + Motivating Actions
    if completed >= 3:
        return "Excellent productivity! You’re crushing your weekly goals. Keep it up!"
    elif completed == 2:
        return "Nice work! You’re building momentum for the week."
    elif completed == 1:
        return "Good start! Keep organizing your week."
    elif total_due == 0:
        return "It's a fresh week! Start by planning your tasks for the days ahead."
    elif missed > 0:
        return "You have overdue tasks this week. Review scheduling accuracy and consider setting earlier reminders to improve responsiveness."
    elif snoozed > 3:
        return "Frequent snoozing detected. Consider adjusting task timing or workload distribution to improve execution consistency."
    elif high_prio_rate >= 50:
        return "You assigned many high-priority tasks this week. Ensure they are distributed properly to avoid overload and stress."
    elif completion_rate >= 80:
        return "Excellent productivity this week. You completed most of your scheduled tasks. Your time management is consistent and effective."
    else:
        return "Your priority distribution is balanced. Small steps lead to big results. Stay consistent this week."

def generate_monthly_insight(db_path, start_dt, completed, created, snoozed, sent):
    """Generates general, non-personal behavioral insights for the 30-day period."""
    import sqlite3
    from datetime import datetime
    
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    
    start_iso = start_dt.isoformat()
    end_iso = datetime.utcnow().isoformat()
    
    from datetime import timedelta
    
    # Calculate Previous Month stats to determine Trends
    prev_end = start_dt
    prev_start = prev_end - timedelta(days=30)
    prev_start_iso = prev_start.isoformat()
    prev_end_iso = prev_end.isoformat()
    
    try:
        cur.execute("SELECT COUNT(*) FROM tasks WHERE status='completed' AND completed_iso >= ? AND completed_iso < ?", (prev_start_iso, prev_end_iso))
        prev_completed = cur.fetchone()[0]
    except: prev_completed = 0
    
    try:
        cur.execute("SELECT COUNT(*) FROM tasks WHERE due_iso >= ? AND due_iso < ? AND status != 'completed'", (start_iso, end_iso))
        curr_missed = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM tasks WHERE due_iso >= ? AND due_iso < ? AND status != 'completed'", (prev_start_iso, prev_end_iso))
        prev_missed = cur.fetchone()[0]
    except:
        curr_missed = 0
        prev_missed = 0
        
    try:
        cur.execute("SELECT COUNT(*) FROM tasks WHERE created_iso >= ? AND created_iso < ?", (prev_start_iso, prev_end_iso))
        prev_created = cur.fetchone()[0]
    except: prev_created = 0
    
    conn.close()
    
    curr_rate = int((completed / created) * 100) if created > 0 else 0
    prev_rate = int((prev_completed / prev_created) * 100) if prev_created > 0 else 0

    # Trend and Consistency AI Engine Scenarios
    if curr_rate > prev_rate and curr_rate > 0:
        diff = curr_rate - prev_rate
        return f"Compared to last month, your completion rate improved by {diff}%. Productivity momentum is increasing."
    elif curr_missed > prev_missed and curr_missed > 0:
        return "Overdue tasks increased this month. Review planning strategy for better time allocation."
    elif snoozed > 5:
        return "Persistent snoozing detected this month. Try breaking tasks down into smaller, immediately actionable steps."
    elif completed > (created * 0.7) and created > 5:
        return "Incredible monthly consistency! Executing your plan is paying off massively."
    else:
        return "Steady progress compounds over 30 days! Balance your planning with active completion."
