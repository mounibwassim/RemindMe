import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.email_service import send_email
from backend.config import SMTP_USER

def verify_smtp():
    print(f"Testing SMTP Configuration for user: {SMTP_USER}")
    
    if "your_email" in SMTP_USER:
        print("ERROR: Please update backend/config.py with real SMTP credentials.")
        return

    success, error = send_email(SMTP_USER, "Test Email from RemindMe", "This is a test email to verify SMTP configuration.")
    
    if success:
        print("SUCCESS: Email sent successfully!")
    else:
        print(f"FAILURE: Could not send email. Error: {error}")

if __name__ == "__main__":
    verify_smtp()
