import os, sys
sys.path.insert(0, r'c:\Users\User\Documents\RemindMe')
from dotenv import load_dotenv
load_dotenv(r'c:\Users\User\Documents\RemindMe\backend_api\.env')

def masked(val, name):
    if not val:
        return f"{name}: NOT SET"
    if len(val) > 8:
        return f"{name}: SET ({val[:6]}...{val[-4:]})"
    return f"{name}: SET"

print("=== Email Provider Status (local .env) ===")
print(masked(os.environ.get("SMTP_HOST"), "SMTP_HOST"))
print(masked(os.environ.get("SMTP_PORT"), "SMTP_PORT"))
print(masked(os.environ.get("SMTP_USER"), "SMTP_USER"))
print(masked(os.environ.get("SMTP_PASS"), "SMTP_PASS"))
print(masked(os.environ.get("SMTP_USERNAME"), "SMTP_USERNAME"))
print(masked(os.environ.get("SMTP_PASSWORD"), "SMTP_PASSWORD"))
print(masked(os.environ.get("BREVO_API_KEY"), "BREVO_API_KEY"))
print(masked(os.environ.get("RESEND_API_KEY"), "RESEND_API_KEY"))
print(f"SENDER_EMAIL:    {os.environ.get('SENDER_EMAIL', 'NOT SET')}")
print(f"RESEND_FROM_EMAIL: {os.environ.get('RESEND_FROM_EMAIL', 'NOT SET')}")
print(f"APP_ENV:         {os.environ.get('APP_ENV', 'NOT SET (defaults to development)')}")
