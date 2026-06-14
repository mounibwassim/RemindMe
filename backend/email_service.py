import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

from backend.config import (
    BREVO_API_KEY,
    RESEND_API_KEY,
    RESEND_FROM_EMAIL,
    RESEND_TEST_OWNER_EMAIL,
    SENDER_EMAIL,
    SMTP_HOST,
    SMTP_PASS,
    SMTP_PORT,
    SMTP_USER,
)


def send_email(to_email: str, subject: str, body: str):
    """
    Send an email using configured providers.

    Priority:
      1. SMTP (SMTP_USER/SMTP_PASS or SMTP_USERNAME/SMTP_PASSWORD)
      2. Brevo (BREVO_API_KEY)
      3. Resend with a verified sender domain (RESEND_FROM_EMAIL)

    Resend's default onboarding sender is only used for the configured test
    owner address. It cannot deliver recovery codes to other users.
    """
    logging.info("[Email] Attempting to send email to %s | subject: %s", to_email, subject)
    errors = []

    if SMTP_USER and SMTP_PASS:
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"RemindMe <{SMTP_USER}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_USER, to_email, msg.as_string())

            logging.info("[Email] SMTP sent successfully to %s", to_email)
            return True, None
        except smtplib.SMTPAuthenticationError as e:
            logging.error("[Email] SMTP auth error: %s", e)
            errors.append(f"SMTP auth failed: {e}")
        except Exception as e:
            logging.error("[Email] SMTP error: %s", e)
            errors.append(f"SMTP failed: {e}")
    else:
        logging.warning("[Email] SMTP skipped: SMTP_USER/SMTP_PASS are not configured.")

    if BREVO_API_KEY:
        try:
            response = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={"api-key": BREVO_API_KEY, "Content-Type": "application/json"},
                json={
                    "sender": {"name": "RemindMe", "email": SENDER_EMAIL},
                    "to": [{"email": to_email}],
                    "subject": subject,
                    "textContent": body,
                },
                timeout=10,
            )
            logging.info("[Email] Brevo response: %s %s", response.status_code, response.text[:200])
            if response.status_code in (200, 201, 202):
                logging.info("[Email] Brevo sent successfully to %s", to_email)
                return True, None
            errors.append(f"Brevo error {response.status_code}: {response.text[:200]}")
        except Exception as e:
            logging.error("[Email] Brevo request failed: %s", e)
            errors.append(f"Brevo failed: {e}")

    if RESEND_API_KEY:
        resend_from = None
        if RESEND_FROM_EMAIL:
            resend_from = f"RemindMe <{RESEND_FROM_EMAIL}>"
        elif to_email.strip().lower() == (RESEND_TEST_OWNER_EMAIL or "").strip().lower():
            resend_from = "RemindMe <onboarding@resend.dev>"

        if not resend_from:
            errors.append(
                "Resend testing mode can only email the Resend account owner. "
                "Configure SMTP, Brevo, or RESEND_FROM_EMAIL from a verified Resend domain."
            )
        else:
            try:
                response = requests.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {RESEND_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": resend_from,
                        "to": [to_email],
                        "subject": subject,
                        "text": body,
                    },
                    timeout=10,
                )
                logging.info("[Email] Resend response: %s %s", response.status_code, response.text[:200])
                if response.status_code in (200, 201, 202):
                    logging.info("[Email] Resend sent successfully to %s", to_email)
                    return True, None
                if response.status_code == 403 and "testing emails" in response.text.lower():
                    errors.append(
                        "Resend testing mode can only email the Resend account owner. "
                        "Configure SMTP, Brevo, or a verified Resend domain."
                    )
                else:
                    errors.append(f"Resend error {response.status_code}: {response.text[:200]}")
            except Exception as e:
                logging.error("[Email] Resend request failed: %s", e)
                errors.append(f"Resend failed: {e}")

    combined = " | ".join(errors) if errors else "No email provider is configured."
    logging.error("[Email] All delivery methods failed for %s. Errors: %s", to_email, combined)
    return False, combined


def send_recovery_email(to_email: str, link: str = None):
    """Convenience wrapper for password recovery emails."""
    subject = "RemindMe - Password Recovery"

    if link:
        body = (
            "Hello,\n\n"
            "We received a request to reset your RemindMe password.\n\n"
            f"Click the link below to reset your password:\n{link}\n\n"
            "If you did not request this, please ignore this email.\n"
        )
    else:
        body = (
            "We received a request to reset your RemindMe password.\n"
            "Use the recovery code shown in the app to reset it.\n\n"
            "If you did not request this, please ignore this email."
        )
    return send_email(to_email, subject, body)
