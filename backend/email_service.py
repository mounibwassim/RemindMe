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
        logging.error("SMTP Configuration missing in config.py")
        return False, "SMTP Configuration missing in config.py"

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        logging.info(f"Attempting to connect to SMTP server {SMTP_HOST}:{SMTP_PORT}")
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        
        # Validate TLS connection
        status, response = server.starttls()
        if status != 220:
            logging.error(f"Failed to establish secure TLS connection: {status} {response}")
            return False, "Failed to establish secure TLS connection"
            
        logging.info("TLS connection established securely.")
        
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        logging.info("SMTP authentication successful.")
        
        text = msg.as_string()
        server.sendmail(SMTP_USERNAME, to_email, text)
        server.quit()
        
        logging.info(f"Email successfully sent to {to_email}")
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
