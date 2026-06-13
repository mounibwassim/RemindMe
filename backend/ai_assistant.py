import requests
import json
import re
from datetime import datetime, timedelta

# --- GLOBALS ---
GEMINI_API_KEY = "AIzaSyBtoR3GqjwcRRXv68Ij9LnB8BETbPEvBco"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# Use a highly specific, clean help message
OFF_TRACK_MSG = 'I\'m your RemindMe Assistant! 📋\nTell me a task to schedule — try something like:\n• "study tomorrow at 6 pm"\n• "gym on Friday at 8 am"\n• "meeting next Monday at 10 am"'

current_task = {"title": "", "date": "", "time": "", "priority": "Medium", "category": "General"}

GREETINGS_PATTERN = r'^(hi|hello|hey|good morning|good afternoon|good evening|how are you|whats up|what\'s up|sup|greetings)(\s+there|\s+man|\s+bro|\s+assistant|\s+remindme|\s+ai|\s+robot)?\s*[!?.]*$'

# ─────────────────────────────────────────────
# CATEGORY MAP
# ─────────────────────────────────────────────
CATEGORY_KEYWORDS = {
    "Gym":      ["gym", "workout", "fitness", "cardio", "training", "exercise", "lifting", "weight", "calisthenics", "protein", "bodybuilding", "yoga", "pilates", "crossfit", "hiit", "sport", "run", "jogging", "swimming", "boxing", "martial arts"],
    "Study":    ["homework", "exam", "revision", "assignment", "university", "college", "school", "class", "study", "learn", "read", "book", "lecture", "tutorial", "quiz", "test", "library", "textbook"],
    "Work":     ["office", "project", "deadline", "client", "meeting", "report", "presentation", "zoom", "teams", "slack", "sync", "standup", "interview", "email", "contract", "salary", "boss", "work", "job", "career", "manager"],
    "Health":   ["medicine", "doctor", "sleep", "water", "therapy", "health", "dentist", "physio", "vitamin", "meditation", "stress", "mental", "wellness", "clinic", "hospital", "pharmacy", "pill", "diet", "appointment"],
    "Finance":  ["payment", "budget", "salary", "bank", "invoice", "finance", "pay", "money", "bill", "rent", "tax", "spend", "expense", "wallet", "crypto", "stock", "invest", "save", "income", "debt"],
    "Call":     ["call", "phone", "dial", "contact", "talk", "mobile", "facetime", "whatsapp", "skype", "voice", "conference"],
    "Family":   ["mom", "dad", "sister", "brother", "parents", "kids", "children", "son", "daughter", "aunt", "uncle", "cousin", "relative", "family", "wife", "husband"],
    "Social":   ["party", "club", "bar", "event", "concert", "movie", "theater", "show", "gathering", "celebrate", "wedding", "friend", "date", "dinner", "lunch", "coffee", "hangout", "meetup"],
    "Home":     ["clean", "cook", "laundry", "repair", "fix", "garden", "pet", "dog", "cat", "kitchen", "dishes", "vacuum", "mop", "groceries", "market", "house", "furniture"],
    "Gaming":   ["game", "ranked", "steam", "playstation", "ps4", "ps5", "xbox", "nintendo", "pc", "gaming", "discord", "stream", "match", "quest", "level", "boss", "multiplayer", "online", "coop", "raid", "tournament"],
    "Birthday": ["birthday", "cake", "party", "celebration", "gift", "anniversary", "surprise", "present", "born"],
}

TASK_KEYWORDS = [
    kw for kws in CATEGORY_KEYWORDS.values() for kw in kws
] + ["remind", "task", "schedule", "session", "event", "plan", "do", "go to", "go", "visit", "pick up", "drop", "take", "call", "meet", "buy", "start", "finish", "complete"]

TIME_INDICATORS = [
    "today", "tomorrow", "tonight", "at", "pm", "am", "next", "this",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "evening", "morning", "afternoon", "noon", "midnight", "night",
    "in ", "minutes", "hours", "week", "tonight", "asap", "soon"
]

CONFIRM_WORDS = {"yes", "save", "sure", "ok", "confirm", "do it", "create", "y", "absolutely", "yep", "yeah", "yup"}
CANCEL_WORDS  = {"cancel", "stop", "forget it", "restart", "clear", "nevermind", "reset", "no"}

# ─────────────────────────────────────────────
# TIME NORMALIZATION
# ─────────────────────────────────────────────
def _normalize_time(time_str: str) -> str:
    if not time_str:
        return ""
    s = time_str.strip().upper().replace(".", "")
    for fmt in ["%H:%M", "%I:%M %p", "%I %p", "%H:%M:%S", "%I:%M:%S %p"]:
        try:
            return datetime.strptime(s, fmt).strftime("%H:%M")
        except ValueError:
            pass
    m = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(AM|PM)?', s)
    if m:
        try:
            h, minute, ampm = int(m.group(1)), int(m.group(2) or 0), m.group(3)
            if ampm == "PM" and h < 12:
                h += 12
            elif ampm == "AM" and h == 12:
                h = 0
            return f"{h:02d}:{minute:02d}"
        except: pass
    return ""

# ─────────────────────────────────────────────
# LOCAL PARSER — always runs first, no API needed
# ─────────────────────────────────────────────
WEEKDAY_MAP = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6
}

def _parse_date_local(text: str, now: datetime = None) -> str:
    t = text.lower()
    if now is None: now = datetime.now()

    if "today" in t or "tonight" in t:
        return now.strftime("%Y-%m-%d")
    if "tomorrow" in t:
        return (now + timedelta(days=1)).strftime("%Y-%m-%d")

    # Handle "next week/month/year"
    if "next week" in t: return (now + timedelta(days=7)).strftime("%Y-%m-%d")
    if "next month" in t:
        m, y = (now.month % 12) + 1, now.year + (now.month // 12)
        try: return datetime(y, m, now.day).strftime("%Y-%m-%d")
        except: return datetime(y, m, 28).strftime("%Y-%m-%d")
    if "next year" in t:
        return datetime(now.year + 1, now.month, now.day).strftime("%Y-%m-%d")

    # Handle "in X days/weeks"
    m = re.search(r'in (\d+)\s+day', t)
    if m: return (now + timedelta(days=int(m.group(1)))).strftime("%Y-%m-%d")
    m = re.search(r'in (\d+)\s+week', t)
    if m: return (now + timedelta(weeks=int(m.group(1)))).strftime("%Y-%m-%d")

    # Handle DD/MM or DD/MM/YYYY or DD-MM-YYYY
    m = re.search(r'\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b', t)
    if m:
        try:
            d, mon = int(m.group(1)), int(m.group(2))
            y = int(m.group(3)) if m.group(3) else now.year
            if y < 100: y += 2000
            return datetime(y, mon, d).strftime("%Y-%m-%d")
        except: pass

    # Month names: "23 may", "may 23", "23rd may", "23 of may", "june 23"
    months = [
        ("jan", 1), ("january", 1), ("feb", 2), ("february", 2),
        ("mar", 3), ("march", 3), ("apr", 4), ("april", 4),
        ("may", 5), ("jun", 6), ("june", 6), ("jul", 7), ("july", 7),
        ("aug", 8), ("august", 8), ("sep", 9), ("september", 9),
        ("oct", 10), ("october", 10), ("nov", 11), ("november", 11),
        ("dec", 12), ("december", 12)
    ]
    # Sort by length descending to match longest first (e.g. "june" before "jun")
    months.sort(key=lambda x: len(x[0]), reverse=True)

    for m_name, m_idx in months:
        if m_name in t:
            # Check "23rd may", "23 may", "23 of may"
            m2 = re.search(rf'(\d{{1,2}})(?:st|nd|rd|th)?(?:\s+of)?\s+{m_name}\b', t)
            # Check "may 23", "may 23rd"
            m3 = re.search(rf'\b{m_name}\s+(\d{{1,2}})(?:st|nd|rd|th)?', t)
            day = int(m2.group(1) if m2 else (m3.group(1) if m3 else 0))
            if day:
                y = now.year
                # Check for year "may 23 2026"
                m4 = re.search(rf'{m_name}\s+{day}\s+(\d{{4}})', t)
                if m4: y = int(m4.group(1))
                try:
                    res_date = datetime(y, m_idx, day)
                    # If the date is in the past, maybe they mean next year?
                    if res_date < now - timedelta(days=1):
                        res_date = datetime(y + 1, m_idx, day)
                    return res_date.strftime("%Y-%m-%d")
                except: pass

    for day_name, day_num in WEEKDAY_MAP.items():
        if day_name in t:
            days_ahead = (day_num - now.weekday() + 7) % 7
            if "next" in t:
                if days_ahead == 0: days_ahead = 7
            elif "this" in t:
                # If it's "this monday" and today is monday, it's today (0)
                pass
            else:
                # Default to nearest future day
                if days_ahead == 0: days_ahead = 7
            return (now + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    return ""

def _parse_time_local(text: str, now: datetime = None) -> str:
    t = text.lower()
    if now is None: now = datetime.now()
    named = {"noon": "12:00", "midnight": "00:00", "morning": "08:00",
             "afternoon": "14:00", "evening": "18:00", "tonight": "20:00", "night": "21:00"}
    
    # Handle "in X hours"
    m = re.search(r'in (\d+)\s+hour', t)
    if m:
        future = now + timedelta(hours=int(m.group(1)))
        return future.strftime("%H:%M")

    # Handle "6 in the evening", "8 in the morning"
    m = re.search(r'(\d{1,2})\s+in the\s+(morning|afternoon|evening|night)', t)
    if m:
        h = int(m.group(1))
        period = m.group(2)
        if period in ["afternoon", "evening", "night"] and h < 12: h += 12
        if period == "morning" and h == 12: h = 0
        return f"{h:02d}:00"

    # Handle "0830", "1800"
    m = re.search(r'\b(\d{2})(\d{2})\b', t)
    if m and not t.startswith("20"): # Avoid matching year 2026
        h, mn = int(m.group(1)), int(m.group(2))
        if 0 <= h < 24 and 0 <= mn < 60:
            return f"{h:02d}:{mn:02d}"

    # Try more specific formats first: "at 5pm", "5:30", "5pm"
    # 1. Look for HH:MM format
    m = re.search(r'\b(\d{1,2}):(\d{2})(?:\s*(am|pm))?\b', t)
    if m:
        h = int(m.group(1))
        minute = int(m.group(2))
        ampm = (m.group(3) or "").lower()
        if ampm == "pm" and h < 12: h += 12
        elif ampm == "am" and h == 12: h = 0
        return f"{h:02d}:{minute:02d}"

    # 2. Look for "at X", "X pm", "X am"
    m = re.search(r'(?:at\s+)?(\d{1,2})\s*(am|pm)\b', t)
    if m:
        h = int(m.group(1))
        ampm = m.group(2).lower()
        if ampm == "pm" and h < 12: h += 12
        elif ampm == "am" and h == 12: h = 0
        return f"{h:02d}:00"

    # 3. Last resort: "at X" (without am/pm)
    m = re.search(r'\bat\s+(\d{1,2})\b', t)
    if m:
        h = int(m.group(1))
        if h < 8: h += 12 # Assume evening if small number like "at 5"
        return f"{h:02d}:00"

    for kw, val in named.items():
        if kw in t: return val
    return ""

def _detect_category(text: str) -> str:
    t = text.lower()
    for cat in ["Family", "Call", "Social", "Finance", "Work", "Study", "Gym", "Home"]:
        if any(kw in t for kw in CATEGORY_KEYWORDS.get(cat, [])):
            return cat
    return "General"

def _detect_priority(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["urgent", "asap", "important", "critical", "high"]): return "High"
    if any(w in t for w in ["low", "whenever", "not urgent", "someday"]): return "Low"
    return "Medium"

def sanitize_task_title(title: str) -> str:
    if not title:
        return ""
    words = title.strip().split()
    connector_words = {
        "by", "on", "in", "at", "for", "with", "to", "from", "of", "about",
        "the", "a", "an", "during", "before", "after", "around", "near"
    }

    # Strip leading/trailing prepositions and connector words recursively
    changed = True
    while changed:
        changed = False
        if words and words[-1].lower() in connector_words:
            words.pop()
            changed = True
        if words and words[0].lower() in connector_words:
            words.pop(0)
            changed = True

    t = " ".join(words)
    t = t.strip(" ,.-")
    return t.capitalize() if t else ""


def _build_title(text: str) -> str:
    t = text.strip()

    # Match prepositions/articles preceding the date/time entities
    PREPS = r'\b(?:on|at|by|in|during|for|around|before|after|near|from|to|about|of)\b'
    ARTICLES = r'\b(?:the|a|an)\b'
    PREP_OR_ART = rf'(?:{PREPS}\s+)?(?:{ARTICLES}\s+)?'

    # Date and time entities
    date_time_entities = [
        # durations: in 5 days, in 2 weeks
        r'\bin\s+\d+\s+days?\b',
        r'\bin\s+\d+\s+weeks?\b',
        
        # relative next/this date phrases: next Friday, this morning
        r'\b(?:next|this)\s+(?:week|month|year|morning|afternoon|evening|night|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
        
        # relative day keywords
        r'\b(?:today|tomorrow|tonight)\b',
        
        # dates with month names: 23rd may, may 23, 23 of june
        r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b',
        r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}(?:st|nd|rd|th)?\b',
        
        # weekday names
        r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
        
        # time of day keywords
        r'\b(?:morning|afternoon|evening|night|noon|midnight)\b',
        
        # standard times: 6:30, 6:30 pm, 6:30pm
        r'\b\d{1,2}:\d{2}\s*(?:am|pm)?\b',
        
        # relative/am-pm times: 6 pm, 6pm, 10 am
        r'\b\d{1,2}\s*(?:am|pm)\b',
        
        # raw hour numbers preceded by at or by: at 5, by 6
        r'\b(?:at|by)\s+\d{1,2}\b'
    ]

    # Combine entities
    combined_pattern = '|'.join(date_time_entities)
    
    # Complete pattern: optionally preceded by prep + article, then the entity
    strip_pattern = re.compile(rf'(?:{PREP_OR_ART})?(?:{combined_pattern})', re.IGNORECASE)

    # 1 & 2. Remove matched date/time entities and their prep phrases
    t = re.sub(strip_pattern, '', t)

    # Strip generic action verbs from start of title
    t = re.sub(r'^(remind me to|remind me|please|i need to|i want to|schedule|add|create|set)\s+', '', t, flags=re.IGNORECASE)
    
    # Clean up excess spaces
    t = re.sub(r'\s+', ' ', t).strip(" ,.-")

    # 3 & 4. Final title sanitizer and validation
    return sanitize_task_title(t)



def _local_parse(text: str, now: datetime):
    t_low = text.lower().strip()
    
    # Use word boundaries for task keywords
    task_pattern = r'\b(' + '|'.join(re.escape(kw) for kw in TASK_KEYWORDS) + r')\b'
    has_task = re.search(task_pattern, t_low) is not None
    
    # Time indicators - exclude 'am'/'pm' from simple string check as they are too common in chatter
    simple_indicators = [ti for ti in TIME_INDICATORS if ti not in ["am", "pm"]]
    time_pattern = r'\b(' + '|'.join(re.escape(ti) for ti in simple_indicators) + r')\b'
    # Also check for specific time patterns like "8am", "8:00"
    has_time = re.search(time_pattern, t_low) or re.search(r'\b\d{1,2}:\d{2}\s*(?:am|pm)?\b|\b\d{1,2}\s*(?:am|pm)\b', t_low)

    # Priority check
    has_prio = any(w in t_low for w in ["high", "medium", "low", "urgent", "asap", "important"])

    # If it's just "I am ..." or "How am ...", it's usually chatter
    if not has_task and not has_time and not has_prio:
        return None
        
    # Extra check: if it starts with "I am" and has no other task indicators, it's chatter
    if t_low.startswith("i am ") and not has_task and not re.search(time_pattern, t_low):
        return None

    return {
        "title":    _build_title(text),
        "date":     _parse_date_local(text, now),
        "time":     _parse_time_local(text, now),
        "priority": _detect_priority(text),
        "category": _detect_category(text),
    }

# ─────────────────────────────────────────────
# GEMINI — optional enhancement
# ─────────────────────────────────────────────
def _call_gemini(prompt: str):
    try:
        # Debug logging
        with open("gemini_debug.log", "a", encoding="utf-8") as f:
            f.write(f"\n--- PROMPT ---\n{prompt}\n")
            
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 256}
        }
        r = requests.post(GEMINI_URL, headers=headers, json=payload, timeout=8)
        if r.status_code == 200:
            res = r.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            with open("gemini_debug.log", "a", encoding="utf-8") as f:
                f.write(f"--- RESPONSE ---\n{res}\n")
            return res
    except Exception as e:
        with open("gemini_debug.log", "a", encoding="utf-8") as f:
            f.write(f"--- ERROR ---\n{e}\n")
        print(f"Gemini Error: {e}")
    return None

def _gemini_enhance(text: str, partial: dict, now: datetime):
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    now_day = now.strftime("%A")
    prompt = f"""
Current datetime: {now_str} ({now_day})
User message: "{text}"
Current partial task: {json.dumps(partial)}

You are an expert scheduler. Extract the EXACT date and time from the user message.
- Today is {now_day}, {now_str}.
- If the user says "in 2 hours", calculate it based on {now_str}.
- "homework on 23 may" -> date: 2026-05-23, time: 10:00 (default)
- "6 in the evening" -> time: 18:00
- "noon" -> time: 12:00
- "midnight" -> time: 00:00
- "23rd of may" -> date: 2026-05-23
- Current year is {now.year}.

Return ONLY a JSON object with 'date' (YYYY-MM-DD) and 'time' (HH:MM).
If a field is already present in 'Current partial task', keep it unless the user message explicitly changes it.
DO NOT ASK QUESTIONS. ONLY RETURN JSON.
"""
    res = _call_gemini(prompt)
    if not res: return partial
    m = re.search(r'\{.*?\}', res, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group())
            if data.get("date") and not partial.get("date"):
                partial["date"] = data["date"]
            if data.get("time") and not partial.get("time"):
                partial["time"] = _normalize_time(data["time"])
        except: pass
    return partial

# ─────────────────────────────────────────────
# MAIN HANDLER
# ─────────────────────────────────────────────
def handle_user_input(text: str, client_time: str = None, _history_ext=None, _draft_ext=None):
    global current_task
    
    # Use client time if provided, otherwise server time
    now = datetime.now()
    if client_time:
        try:
            # Handle ISO8601 from dart (e.g. 2026-05-14T17:39:53.000)
            if 'T' in client_time:
                now = datetime.fromisoformat(client_time.split('.')[0])
        except: pass

    task_draft = _draft_ext if isinstance(_draft_ext, dict) and "title" in _draft_ext else current_task.copy()
    t = text.strip().lower()

    if t in CANCEL_WORDS:
        cleared = {"title": "", "date": "", "time": "", "priority": "Medium", "category": "General"}
        if _draft_ext is None: current_task = cleared
        return {"type": "chat", "response": "Task cleared. " + OFF_TRACK_MSG, "task": cleared}

    # Catch greetings immediately
    if re.match(GREETINGS_PATTERN, t):
        cleared = {"title": "", "date": "", "time": "", "priority": "Medium", "category": "General"}
        if _draft_ext is None: current_task = cleared
        return {"type": "chat", "response": OFF_TRACK_MSG, "task": cleared}

    # --- LOCAL PARSING ---
    # ISOLATION: Remove dates before parsing time
    time_search_text = text
    date_patterns = [
        r'\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',
        r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}',
        r'\b\d{1,2}[/-]\d{1,2}([/-]\d{2,4})?\b'
    ]
    for p in date_patterns:
        time_search_text = re.sub(p, ' [DATE] ', time_search_text, flags=re.IGNORECASE)

    parsed = _local_parse(text, now)
    if parsed is None: parsed = {}
    
    # Special time parsing using isolated string
    iso_time = _parse_time_local(time_search_text, now)
    if iso_time: parsed["time"] = iso_time

    # Reset draft if a new title is explicitly provided
    if parsed.get("title") and task_draft.get("title") and parsed["title"].lower() != task_draft["title"].lower():
        task_draft = {"title": "", "date": "", "time": "", "priority": "Medium", "category": "General"}

    # CRITICAL FIX: Only overwrite date/time if the user isn't just saying "yes" or "ok"
    if t not in CONFIRM_WORDS:
        for field in ["title", "date", "time", "priority"]:
            if parsed.get(field): 
                # If we already have a time, and the new one is suspicious (matched from a date), ignore it
                if field == "time" and task_draft.get("time") and not re.search(r'\d{1,2}(:|\s*(am|pm))', text.lower()):
                    continue
                task_draft[field] = parsed[field]
    
    # Only update category if we found a match OR if title is new
    if parsed.get("category") and (parsed["category"] != "General" or parsed.get("title")):
        task_draft["category"] = parsed["category"]

    # --- CONVERSATIONAL / SMALL TALK HANDLER ---
    if not parsed and not (task_draft.get("title") and t in CONFIRM_WORDS):
        # Clear draft if the message is out of context/chatter and not confirming
        cleared = {"title": "", "date": "", "time": "", "priority": "Medium", "category": "General"}
        if _draft_ext is None: current_task = cleared
        return {"type": "chat", "response": OFF_TRACK_MSG, "task": cleared}

    # --- GEMINI ENHANCEMENT ---
    if task_draft.get("title") and (not task_draft.get("date") or not task_draft.get("time")):
        task_draft = _gemini_enhance(text, task_draft, now)

    if _draft_ext is None: current_task = task_draft

    # --- VALIDATION ---
    if not task_draft.get("title"):
        return {"type": "chat", "response": OFF_TRACK_MSG, "task": task_draft.copy()}
    
    # Check for date and time BEFORE past-date check
    if not task_draft.get("date"):
        return {"type": "chat", "response": f"Got it — '{task_draft['title']}'! 📅 What date? (e.g. 'today', 'tomorrow')", "task": task_draft.copy()}
    if not task_draft.get("time"):
        return {"type": "chat", "response": f"Almost there! ⏰ What time for '{task_draft['title']}'? (e.g. '6 pm')", "task": task_draft.copy()}

    # --- PAST DATE/TIME CHECK ---
    try:
        dt_str = f"{task_draft['date']} {task_draft['time']}"
        target_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        
        # If target is in the past compared to client time
        if target_dt < now - timedelta(minutes=1):
            # Critical block: Clear date/time from draft
            task_draft["date"] = ""
            task_draft["time"] = ""
            if _draft_ext is None: current_task = task_draft
            return {
                "type": "chat",
                "response": f"⚠️ I can't schedule that! The time {dt_str} is in the past. Please tell me a future time for '{task_draft['title']}'. 🚀",
                "task": task_draft.copy()
            }
    except Exception as e:
        print(f"Past validation error: {e}")

    # Priority check
    if task_draft.get("priority") == "Medium" and not parsed.get("priority"):
        return {"type": "task", "response": f"One last thing! 📊 What priority for '{task_draft['title']}'? (Low, Medium, or High)", "task": task_draft.copy()}

    # --- CONFIRMATION STEP ---
    # Ask for confirmation if all fields are present but not confirmed
    if t not in CONFIRM_WORDS:
        response = (
            f"✅ Task detected: '{task_draft['title']}' on {task_draft['date']} at {task_draft['time']}.\n"
            f"Confirm? (yes / cancel) 🚀"
        )
        return {"type": "task", "response": response, "task": task_draft.copy()}

    response = (
        f"✅ Task saved: '{task_draft['title']}' for {task_draft['date']} at {task_draft['time']}."
    )
    return {"type": "ready_to_save", "response": response, "task": task_draft.copy()}

def reset_task_state():
    global current_task
    current_task = {"title": "", "date": "", "time": "", "priority": "Medium", "category": "General"}

def generate_weekly_insight(*args):
    return _call_gemini("Generate a 1-sentence motivational insight about schedule management.") or "Great job organizing your day!"

def generate_monthly_insight(*args):
    return _call_gemini("Generate a 1-sentence monthly motivational insight for task completion.") or "You're building great habits!"
