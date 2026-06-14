import os
import logging
import traceback
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend_api", ".env"))

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
supabase_admin: Client = create_client(url, key)

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("backend_api")

# SMTP Configuration for native mailing
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")

def send_native_email(to_email, otp_code):
    if not SMTP_USER or not SMTP_PASS:
        logger.error("SMTP_USER or SMTP_PASS not set in .env. Cannot send real email.")
        return False
        
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = f"RemindMe - Recovery Code: {otp_code}"
        
        body = f"""
        Hello,
        
        Your 6-digit recovery code for RemindMe is: {otp_code}
        
        Enter this code in the app to reset your password.
        
        If you did not request this, please ignore this email.
        """
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        logger.info("Recovery email sent successfully to %s", to_email)
        return True
    except Exception as e:
        logger.error("Failed to send native email: %s", e)
        return False

# In-memory store for OTPs
pending_otps = {} 

def sign_up_with_email_password(email, password):
    logger.debug("Supabase signup request for email: %s", email)
    try:
        # Use admin API to bypass Supabase SMTP confirmation limits
        response = supabase_admin.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True
        })
        
        # After admin creation, sign in to get the session token
        session_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        data = {
            "localId": session_response.user.id if session_response.user else response.user.id,
            "idToken": session_response.session.access_token if getattr(session_response, 'session', None) else None,
            "email": session_response.user.email if session_response.user else email
        }
        return data, None
    except Exception as e:
        logger.exception("Supabase signup exception")
        error_msg = str(e)
        if "User already registered" in error_msg or "already exists" in error_msg:
            return None, "user_already_exists"
        return None, error_msg

def sign_in_with_email_password(email, password):
    logger.debug("Supabase login request for email: %s", email)
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if not getattr(response, 'session', None):
            return None, "Login successful but no session returned. Please check if your email is confirmed."
        data = {
            "localId": response.user.id,
            "idToken": response.session.access_token,
            "refreshToken": response.session.refresh_token,
            "email": response.user.email
        }
        return data, None
    except Exception as e:
        error_msg = str(e)
        if "Invalid login credentials" in error_msg:
            return None, "invalid login credentials"
        return None, error_msg

from backend.email_service import send_email
from backend.otp_store import generate_and_store_otp, verify_and_consume_otp

def reset_password_email(email, platform='web'):
    logger.info("[Forgot Password] OTP generation initiated for email: %s", email)
    try:
        otp = generate_and_store_otp(email, expiry_minutes=15)
        logger.info("[Forgot Password] Secure 6-digit OTP code generated successfully for %s", email)
        
        # DEVELOPER ALERT: Always print the generated OTP to the server logs
        logger.critical(f"[Forgot Password] DEVELOPER ALERT: OTP for {email} is: {otp}")
        print(f"[Forgot Password] DEVELOPER ALERT: OTP for {email} is: {otp}")
        
        subject = "RemindMe - Your Recovery Code"
        body = f"Hello,\n\nYour 6-digit recovery code is: {otp}\n\nThis code will expire in 15 minutes.\n\nEnter this in the app to reset your password."
        
        logger.info("[Forgot Password] Attempting OTP delivery via HTTP API service to %s...", email)
        success, error = send_email(email, subject, body)
        
        if success:
            logger.info("[Forgot Password] OTP email delivered successfully via HTTP API to %s", email)
            return {"message": "OTP_SENT_TO_EMAIL", "email": email, "info": error}, None
        else:
            logger.error("[Forgot Password] HTTP API email delivery failed: %s", error)
            return None, f"Email delivery failed: {error}"
            
    except Exception as e:
        logger.error("[Forgot Password] Exception during OTP generation/delivery for %s: %s", email, e)
        traceback.print_exc()
        return None, str(e)



def confirm_password_reset(otp_code, new_password, email=None):
    logger.info("[Forgot Password] OTP verification initiated for %s with code: %s", email, otp_code)
    try:
        if not email:
            logger.error("[Forgot Password] Verification failed: Email is missing.")
            return None, "Email is required to confirm password reset in Supabase."
            
        # Check local secure OTP first
        logger.info("[Forgot Password] Checking local SQLite database for OTP verification...")
        if verify_and_consume_otp(email, otp_code):
            logger.info("[Forgot Password] Local SQLite OTP verified successfully for %s. Resetting password...", email)
            # Find the user ID for this email
            user_res = supabase_admin.auth.admin.list_users()
            user = next((u for u in user_res if u.email == email), None)
            if not user:
                logger.error("[Forgot Password] Local reset failed: User %s not found in Supabase Auth records.", email)
                return None, "User not found in Supabase."
            
            # Reset password directly via admin API
            logger.info("[Forgot Password] Requesting Supabase Admin API password reset for user ID %s (%s)...", user.id, email)
            try:
                response = supabase_admin.auth.admin.update_user_by_id(user.id, {"password": new_password})
                logger.info("[Forgot Password] Supabase Admin API password updated successfully for %s.", email)
                return response, None
            except Exception as pe:
                logger.error("[Forgot Password] Supabase Admin API password update failed for %s: %s", email, pe)
                return None, str(pe)

        # Fallback to verifying Supabase OTP
        logger.warning("[Forgot Password] Local SQLite OTP check failed/expired for %s. Trying Supabase verify_otp...", email)
        
        verify_res = None
        verify_error = None
        
        # Sequentially try different verification types to guarantee compatibility
        for otp_type in ["email", "recovery", "magiclink"]:
            try:
                logger.info("[Forgot Password] Attempting Supabase verify_otp with type=%s for %s...", otp_type, email)
                # Initialize a temporary client to avoid polluting the shared client session
                temp_client = create_client(url, key)
                verify_res = temp_client.auth.verify_otp({
                    "email": email,
                    "token": otp_code,
                    "type": otp_type
                })
                if verify_res and verify_res.user:
                    logger.info("[Forgot Password] Supabase verify_otp succeeded with type=%s for %s", otp_type, email)
                    break
            except Exception as e:
                logger.warning("[Forgot Password] Supabase verify_otp failed with type=%s: %s", otp_type, e)
                verify_error = e

        if verify_res and verify_res.user:
            user_id = verify_res.user.id
            logger.info("[Forgot Password] Supabase OTP verified. Resetting password for user ID %s (%s) via admin API...", user_id, email)
            try:
                response = supabase_admin.auth.admin.update_user_by_id(user_id, {"password": new_password})
                logger.info("[Forgot Password] Supabase Admin API password updated successfully for %s.", email)
                return response, None
            except Exception as pe:
                logger.error("[Forgot Password] Supabase Admin API password update failed for %s: %s", email, pe)
                return None, str(pe)
            
        logger.error("[Forgot Password] All OTP verification methods failed for %s.", email)
        err_detail = str(verify_error) if verify_error else "Invalid or expired recovery code."
        return None, f"Invalid or expired recovery code. Details: {err_detail}"
    except Exception as e:
        import traceback
        logger.error("[Forgot Password] OTP Verification failed with exception: %s\n%s", e, traceback.format_exc())
        return None, str(e)

def update_password(access_token, new_password):
    try:
        response = supabase.auth.update_user({"password": new_password})
        return response, None
    except Exception as e:
        return None, str(e)

def resend_verification_email(email):
    try:
        supabase.auth.resend({"type": "signup", "email": email})
        return {"message": "Success"}, None
    except Exception as e:
        return None, str(e)

def get_user_data(access_token):
    try:
        response = supabase.auth.get_user(access_token)
        return {
            "localId": response.user.id,
            "email": response.user.email,
            "displayName": response.user.user_metadata.get("full_name")
        }
    except Exception as e:
        return None
