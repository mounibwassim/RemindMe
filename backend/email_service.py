import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.config import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD

def send_email(to_email, subject, body):
    """
    Sends an email using the configured SMTP server.
    Returns: (bool success, str error_message)
    """
    if not SMTP_SERVER or not SMTP_USER or not SMTP_PASSWORD:
        return False, "SMTP Configuration missing in config.py"

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SMTP_USER, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_USER, to_email, text)
        server.quit()
        return True, None
    except Exception as e:
        logging.error(f"SMTP Error: {e}")
        return False, str(e)

def send_recovery_email(to_email, link=None):
    subject = "Password Reset Request"
    if link:
        body = f"Click the following link to reset your password:\n\n{link}\n\nIf you did not request this, please ignore this email."
    else:
        # Fallback if we can't generate a link (e.g. Firebase restriction)
        body = "We received a request to reset your password. Use the code provided by the app or contact support."
        
    return send_email(to_email, subject, body)
