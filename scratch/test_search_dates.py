from dateparser.search import search_dates
from datetime import datetime

settings = {
    'TIMEZONE': 'local',
    'RETURN_AS_TIMEZONE_AWARE': False
}

text = "meeting tomorrow at 9 am"
found = search_dates(text, settings=settings)
print(f"Text: '{text}' -> Found: {found}")

text2 = "next Friday at 3 pm"
found2 = search_dates(text2, settings=settings)
print(f"Text: '{text2}' -> Found: {found2}")
