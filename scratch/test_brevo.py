"""
Test Brevo HTTP API email delivery.
Brevo uses HTTP (not SMTP), so it works from Render.
"""
import requests

BREVO_API_KEY = "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"
SENDER_EMAIL = "mounibwassimm@gmail.com"  # Must be verified sender in Brevo
TO_EMAIL = "mounibwassimm@gmail.com"      # Send test to yourself

print(f"Testing Brevo API to: {TO_EMAIL}")

response = requests.post(
    "https://api.brevo.com/v3/smtp/email",
    headers={
        "api-key": BREVO_API_KEY,
        "Content-Type": "application/json"
    },
    json={
        "sender": {"name": "RemindMe", "email": SENDER_EMAIL},
        "to": [{"email": TO_EMAIL}],
        "subject": "RemindMe - Brevo Test",
        "textContent": "If you receive this email, Brevo is configured correctly for RemindMe password recovery.",
    },
    timeout=15,
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code in (200, 201, 202):
    print("\nSUCCESS: Brevo email sent! Check your inbox.")
elif response.status_code == 401:
    print("\nERROR 401: Unrecognized IP or invalid API key.")
    print("Fix: Go to https://app.brevo.com/security/authorised-ips and authorize the IP.")
elif response.status_code == 400:
    print("\nERROR 400: Sender email not verified in Brevo.")
    print("Fix: Go to https://app.brevo.com/senders and add/verify the sender email.")
else:
    print(f"\nUnexpected error {response.status_code}")
