import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.config import SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD

def send_email(to_email, subject, body):
    """
    Sends an email using the configured SMTP server.
    Returns: (bool success, str error_message)
    """
    if not SMTP_HOST or not SMTP_USERNAME or not SMTP_PASSWORD:
        logging.error("[Forgot Password] SMTP Send: Configuration missing in config.py")
        return False, "SMTP Configuration missing in config.py"

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        logging.info(f"[Forgot Password] SMTP Send: Attempting to connect to SMTP server {SMTP_HOST}:{SMTP_PORT} using user {SMTP_USERNAME}...")
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
        logging.info("[Forgot Password] SMTP Send: Connected. Starting STARTTLS...")
        
        # Validate TLS connection
        status, response = server.starttls()
        logging.info(f"[Forgot Password] SMTP Send: STARTTLS response status={status}, msg={response}")
        if status != 220:
            logging.error(f"[Forgot Password] SMTP Send: Failed to establish secure TLS connection: {status} {response}")
            return False, "Failed to establish secure TLS connection"
            
        logging.info("[Forgot Password] SMTP Send: TLS connection established securely. Logging in...")
        
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        logging.info("[Forgot Password] SMTP Send: SMTP authentication successful. Sending message...")
        
        text = msg.as_string()
        server.sendmail(SMTP_USERNAME, to_email, text)
        server.quit()
        
        logging.info(f"[Forgot Password] SMTP Send: Email successfully sent to {to_email}")
        return True, None
    except smtplib.SMTPAuthenticationError as e:
        logging.error(f"SMTP Authentication Error: {e}")
        return False, "SMTP authentication failed. Verify Gmail App Password."
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
