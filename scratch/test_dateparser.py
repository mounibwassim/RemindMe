import dateparser
from datetime import datetime

settings = {
    'TIMEZONE': 'local',
    'RETURN_AS_TIMEZONE_AWARE': False
}

text = "meeting tomorrow at 9 am"
dt = dateparser.parse(text, settings=settings)
print(f"Text: '{text}' -> Result: {dt}")

text2 = "tomorrow at 9 am"
dt2 = dateparser.parse(text2, settings=settings)
print(f"Text: '{text2}' -> Result: {dt2}")

text3 = "next Friday at 3 pm"
dt3 = dateparser.parse(text3, settings=settings)
print(f"Text: '{text3}' -> Result: {dt3}")
