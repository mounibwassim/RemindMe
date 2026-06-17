"""
Test if Gmail SMTP works from this machine (local) to confirm credentials are valid.
Then we diagnose why it fails on Render.
"""
import os, sys, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
sys.path.insert(0, r'c:\Users\User\Documents\RemindMe')
from dotenv import load_dotenv
load_dotenv(r'c:\Users\User\Documents\RemindMe\backend_api\.env')

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER") or os.environ.get("SMTP_USERNAME")
SMTP_PASS = os.environ.get("SMTP_PASS") or os.environ.get("SMTP_PASSWORD")

print(f"Testing SMTP to {SMTP_HOST}:{SMTP_PORT} as {SMTP_USER}")

try:
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = SMTP_USER  # Send to yourself as a test
    msg['Subject'] = "RemindMe SMTP Test"
    msg.attach(MIMEText("This is a test email from the RemindMe password reset system.", 'plain'))

    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(SMTP_USER, SMTP_PASS)
    server.sendmail(SMTP_USER, SMTP_USER, msg.as_string())
    server.quit()
    print("SUCCESS: SMTP email sent! Check your inbox.")
except smtplib.SMTPAuthenticationError as e:
    print(f"AUTH FAILED: {e}")
    print("Fix: Use a Gmail App Password (not your Google account password)")
except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")
