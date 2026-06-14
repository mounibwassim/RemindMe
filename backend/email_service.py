import logging
import requests
from backend.config import BREVO_API_KEY, RESEND_API_KEY

def send_email(to_email, subject, body):
    """
    Sends an email using the most reliable HTTPS API method available:
    1. Brevo HTTP API (if BREVO_API_KEY is configured)
    2. Resend HTTP API (if RESEND_API_KEY is configured)
    3. FormSubmit keyless HTTP API (fallback if no keys are configured)
    Returns: (bool success, str error_message)
    """
    logging.info(f"[Forgot Password] [Email Service] Attempting to send email to {to_email}...")

    # 1. Try Brevo HTTP API
    if BREVO_API_KEY:
        logging.info("[Forgot Password] [Email Service] Found BREVO_API_KEY. Attempting HTTP delivery via Brevo...")
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "api-key": BREVO_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "sender": {"name": "RemindMe", "email": "mounibwassimm@gmail.com"},
            "to": [{"email": to_email}],
            "subject": subject,
            "textContent": body
        }
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=10)
            logging.info(f"[Forgot Password] [Email Service] Brevo API Response: status={r.status_code}, body={r.text}")
            if r.status_code in [200, 201, 202]:
                logging.info(f"[Forgot Password] [Email Service] Email sent successfully via Brevo to {to_email}")
                return True, None
            return False, f"Brevo returned error status {r.status_code}: {r.text}"
        except Exception as e:
            logging.error(f"[Forgot Password] [Email Service] Brevo API request failed: {e}")
            return False, f"Brevo request failed: {e}"

    # 2. Try Resend HTTP API
    if RESEND_API_KEY:
        logging.info("[Forgot Password] [Email Service] Found RESEND_API_KEY. Attempting HTTP delivery via Resend...")
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        }
        # Resend's free tier sandbox requires sending from onboarding@resend.dev
        payload = {
            "from": "RemindMe <onboarding@resend.dev>",
            "to": [to_email],
            "subject": subject,
            "text": body
        }
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=10)
            logging.info(f"[Forgot Password] [Email Service] Resend API Response: status={r.status_code}, body={r.text}")
            if r.status_code in [200, 201, 202]:
                logging.info(f"[Forgot Password] [Email Service] Email sent successfully via Resend to {to_email}")
                return True, None
            return False, f"Resend returned error status {r.status_code}: {r.text}"
        except Exception as e:
            logging.error(f"[Forgot Password] [Email Service] Resend API request failed: {e}")
            return False, f"Resend request failed: {e}"

    # 3. Fallback: FormSubmit Keyless HTTP API (uses HTTPS port 443, not blocked by Render)
    logging.info("[Forgot Password] [Email Service] No API keys (Brevo/Resend) configured. Trying FormSubmit keyless fallback...")
    url = f"https://formsubmit.co/ajax/{to_email}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://remindme.onrender.com"
    }
    payload = {
        "name": "RemindMe Recovery",
        "message": body
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        logging.info(f"[Forgot Password] [Email Service] FormSubmit API Response: status={r.status_code}, body={r.text}")
        if r.status_code == 200:
            res_data = r.json()
            if res_data.get("success") == "true" or res_data.get("success") is True:
                logging.info(f"[Forgot Password] [Email Service] Email sent successfully via FormSubmit to {to_email}")
                return True, None
            elif "Activation" in res_data.get("message", ""):
                logging.warning(f"[Forgot Password] [Email Service] FormSubmit requires activation for {to_email}. Activation email sent.")
                return True, "FormSubmit activation email sent. Please click the link inside it to activate recovery delivery."
            return False, f"FormSubmit failed: {res_data.get('message')}"
        return False, f"FormSubmit returned HTTP status {r.status_code}"
    except Exception as e:
        logging.error(f"[Forgot Password] [Email Service] FormSubmit request failed: {e}")
        return False, f"FormSubmit request failed: {e}"

def send_recovery_email(to_email, link=None):
    subject = "Password Reset Request"
    if link:
        body = f"Click the following link to reset your password:\n\n{link}\n\nIf you did not request this, please ignore this email."
    else:
        body = "We received a request to reset your password. Use the code provided by the app or contact support."
        
    return send_email(to_email, subject, body)


