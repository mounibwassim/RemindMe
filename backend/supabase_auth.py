import os
import logging
import traceback
from supabase import create_client, Client
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend_api", ".env"))

url: str = os.environ.get("SUPABASE_URL")
# Primary anon/public key used for client-side operations
key: str = os.environ.get("SUPABASE_KEY")
# Service role key for admin operations (MUST be set in production env)
service_role_key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY") or key
supabase: Client = create_client(url, key)
# Use service role key for admin operations to ensure proper privileges
supabase_admin: Client = create_client(url, service_role_key)

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

def _admin_auth_headers():
    return {
        "Authorization": f"Bearer {service_role_key}",
        "apikey": service_role_key,
    }

def _normalize_admin_users(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        users = payload.get("users")
        if isinstance(users, list):
            return users
        user = payload.get("user")
        if isinstance(user, dict):
            return [user]
        if payload.get("id") and payload.get("email"):
            return [payload]
    return []

def get_auth_user_by_email(email):
    email_clean = (email or "").strip().lower()
    if not email_clean:
        return None, "Email is required."

    try:
        admin_users_endpoint = f"{url.rstrip('/')}/auth/v1/admin/users"
        resp = requests.get(
            admin_users_endpoint,
            headers=_admin_auth_headers(),
            params={"page": 1, "per_page": 1000},
            timeout=10,
        )
        if resp.status_code != 200:
            logger.error("[Auth] Supabase admin user lookup failed (%s): %s", resp.status_code, resp.text)
            return None, f"User lookup failed: {resp.status_code}"

        for user_obj in _normalize_admin_users(resp.json()):
            u_email = (user_obj.get("email") or user_obj.get("user", {}).get("email") or "").strip().lower()
            if u_email == email_clean:
                return user_obj, None

        return None, "User not found in Supabase."
    except Exception as e:
        logger.error("[Auth] Supabase admin user lookup failed for %s: %s", email_clean, e)
        return None, str(e)

def _auth_user_id(user_obj):
    if not user_obj:
        return None
    return user_obj.get("id") or user_obj.get("user", {}).get("id")

def _update_auth_user_password(user_id, new_password):
    if not user_id:
        return None, "User lookup failed."
    try:
        response = supabase_admin.auth.admin.update_user_by_id(user_id, {"password": new_password})
        return response, None
    except Exception as sdk_error:
        logger.warning("[Auth] Supabase SDK password update failed for %s: %s. Trying REST fallback.", user_id, sdk_error)

    try:
        update_endpoint = f"{url.rstrip('/')}/auth/v1/admin/users/{user_id}"
        headers = {**_admin_auth_headers(), "Content-Type": "application/json"}
        upd = requests.patch(update_endpoint, headers=headers, json={"password": new_password}, timeout=10)
        if upd.status_code in (200, 204):
            return upd.json() if upd.text else {}, None
        logger.error("[Auth] Supabase REST password update failed for %s: %s %s", user_id, upd.status_code, upd.text)
        return None, f"Password update failed: {upd.status_code} {upd.text}"
    except Exception as rest_error:
        logger.error("[Auth] Supabase REST password update failed for %s: %s", user_id, rest_error)
        return None, str(rest_error)

def _update_password_and_verify_login(email, user_id, new_password):
    data, update_error = _update_auth_user_password(user_id, new_password)
    if update_error:
        return None, update_error

    login_data, login_error = sign_in_with_email_password(email, new_password)
    if login_error:
        logger.error(
            "[Forgot Password] Password update verification failed for %s: %s",
            email,
            login_error,
        )
        return None, f"Password was updated but login verification failed: {login_error}"

    logger.info("[Forgot Password] Password update verified by signing in as %s.", email)
    return data or login_data, None

def reset_password_email(email, platform='web'):
    logger.info("[Forgot Password] OTP generation initiated for email: %s", email)
    # Reload .env at runtime so OTP_WHITELIST changes take effect without
    # requiring a full backend restart (helpful during troubleshooting).
    try:
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend_api", ".env"))
    except Exception:
        pass
    try:
        user_obj, lookup_error = get_auth_user_by_email(email)
        if lookup_error or not user_obj:
            logger.warning("[Forgot Password] Refusing OTP for unregistered email %s: %s", email, lookup_error)
            return None, "This email is not registered."

        otp = generate_and_store_otp(email, expiry_minutes=15)
        logger.info("[Forgot Password] Secure 6-digit OTP code generated successfully for %s", email)
        
        # DEVELOPER ALERT: Always print the generated OTP to the server logs
        logger.critical(f"[Forgot Password] DEVELOPER ALERT: OTP for {email} is: {otp}")
        print(f"[Forgot Password] DEVELOPER ALERT: OTP for {email} is: {otp}")
        
        subject = "RemindMe - Your Recovery Code"
        body = f"Hello,\n\nYour 6-digit recovery code is: {otp}\n\nThis code will expire in 15 minutes.\n\nEnter this in the app to reset your password."

        # Deliver the exact app OTP. Supabase's recovery-link email is intentionally
        # not used here because the Flutter flow expects a 6-digit code.
        logger.info("[Forgot Password] Attempting OTP delivery via HTTP API service to %s...", email)
        success, error = send_email(email, subject, body)
        if success:
            logger.info("[Forgot Password] OTP email delivered successfully via HTTP API to %s", email)
            resp = {"message": "OTP_SENT_TO_EMAIL", "email": email, "info": error}
            # In non-production environments, return the OTP to help debugging/testing
            if os.environ.get("APP_ENV", "development") != "production":
                resp["developer_otp"] = otp
            return resp, None
        else:
            logger.error("[Forgot Password] HTTP API email delivery failed: %s", error)
            # Keep the developer log for local debugging, but do not report success
            # unless the user can actually receive the code by email.
            logger.critical(f"[Forgot Password] DEVELOPER FALLBACK: OTP for {email} is: {otp}")

            # In development, always expose the OTP for testing convenience.
            if os.environ.get("APP_ENV", "development") != "production":
                return {"message": "OTP_SENT_TO_EMAIL", "email": email, "info": error, "developer_otp": otp}, None

            # Production: allow an explicit whitelist of emails to receive the
            # developer OTP in the response when external delivery fails. This
            # is a controlled escape hatch for troubleshooting accounts that
            # cannot receive mail due to provider/network issues.
            otp_whitelist = os.environ.get("OTP_WHITELIST", "")
            try:
                whitelist = [e.strip().lower() for e in otp_whitelist.split(",") if e.strip()]
            except Exception:
                whitelist = []

            if email.strip().lower() in whitelist:
                logger.warning(
                    "[Forgot Password] Email delivery failed but '%s' is in OTP_WHITELIST — returning developer_otp in response.",
                    email,
                )
                return {"message": "OTP_SENT_TO_EMAIL", "email": email, "info": error, "developer_otp": otp}, None

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
            user_obj, lookup_error = get_auth_user_by_email(email)
            if lookup_error or not user_obj:
                logger.error("[Forgot Password] Local reset failed: User %s not found in Supabase Auth records. Error: %s", email, lookup_error)
                return None, "User not found in Supabase."

            data, update_error = _update_password_and_verify_login(email, _auth_user_id(user_obj), new_password)
            if update_error:
                return None, update_error
            logger.info("[Forgot Password] Supabase Admin API password updated successfully for %s.", email)
            return data, None

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
            data, update_error = _update_password_and_verify_login(email, user_id, new_password)
            if update_error:
                return None, update_error
            logger.info("[Forgot Password] Supabase Admin API password updated successfully for %s.", email)
            return data, None
            
        logger.error("[Forgot Password] All OTP verification methods failed for %s.", email)
        err_detail = str(verify_error) if verify_error else "Invalid or expired recovery code."
        return None, f"Invalid or expired recovery code. Details: {err_detail}"
    except Exception as e:
        import traceback
        logger.error("[Forgot Password] OTP Verification failed with exception: %s\n%s", e, traceback.format_exc())
        return None, str(e)

def update_password(access_token, new_password):
    try:
        user_data = get_user_data(access_token)
        if not user_data or not user_data.get("localId"):
            return None, "Invalid user session."
        user_id = user_data["localId"]
        response = supabase_admin.auth.admin.update_user_by_id(user_id, {"password": new_password})
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


def update_profile(access_token_or_tokenless, display_name):
    """Update user's display name (stored in user_metadata.full_name) via admin API.
    If an access token is provided, use it to determine the user id; otherwise fails back to no-op.
    """
    try:
        # Try to resolve user id from provided access token
        user_id = None
        try:
            user = supabase.auth.get_user(access_token_or_tokenless)
            user_id = user.user.id if getattr(user, 'user', None) else None
        except Exception:
            user_id = None

        if not user_id:
            logger.warning("[Profile] Could not resolve user id from access token to update profile.")
            return None, "Could not resolve user id"

        admin_users_endpoint = f"{url.rstrip('/')}/auth/v1/admin/users/{user_id}"
        headers = {
            "Authorization": f"Bearer {service_role_key}",
            "apikey": service_role_key,
            "Content-Type": "application/json",
        }
        payload = {"user_metadata": {"full_name": display_name}}
        resp = requests.patch(admin_users_endpoint, json=payload, headers=headers, timeout=8)
        if resp.status_code in (200, 204):
            return resp.json() if resp.text else {}, None
        return None, f"Profile update failed: {resp.status_code} {resp.text}"
    except Exception as e:
        logger.error("[Profile] update_profile failed: %s", e)
        return None, str(e)


# ------------------ Username mapping helpers (replace Firebase RTDB usage) ------------------
def _local_usernames_path():
    try:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend_api", "data")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "usernames.json")
    except Exception:
        return None

def save_username_mapping(username, email, uid, metadata=None):
    """Save username mapping locally and to Supabase 'usernames' table (if available)."""
    clean_username = username.strip().lower()
    payload = {"username": clean_username, "email": email, "uid": uid}
    if metadata:
        payload["metadata"] = metadata

    # Save locally
    try:
        local_path = _local_usernames_path()
        if local_path:
            mappings = {}
            if os.path.exists(local_path):
                try:
                    with open(local_path, "r", encoding="utf-8") as f:
                        import json
                        mappings = json.load(f)
                except Exception:
                    mappings = {}
            mappings[clean_username] = payload
            with open(local_path, "w", encoding="utf-8") as f:
                import json
                json.dump(mappings, f, indent=2)
    except Exception as e:
        logger.warning("[UsernameMapping] Local save failed: %s", e)

    # Try saving to Supabase table 'usernames' via admin client
    try:
        res = supabase_admin.table("usernames").upsert(payload, on_conflict="username").execute()
        logger.info("[UsernameMapping] Supabase upsert result: %s", getattr(res, 'data', res))
        return True, None
    except Exception as e:
        logger.warning("[UsernameMapping] Supabase upsert failed: %s", e)
        return True, None


def get_username_data(username):
    query_val = username.strip().lower()
    if "@" in query_val:
        return None, "Email lookup bypasses mapping lookup."

    # 1. Local mirror
    try:
        local_path = _local_usernames_path()
        if local_path and os.path.exists(local_path):
            import json
            with open(local_path, "r", encoding="utf-8") as f:
                mappings = json.load(f)
            if query_val in mappings:
                return mappings[query_val], None
    except Exception as e:
        logger.warning("[UsernameMapping] Local read failed: %s", e)

    # 2. Supabase table lookup
    try:
        res = supabase_admin.table("usernames").select("*").eq("username", query_val).execute()
        data = getattr(res, 'data', None) or res
        if data:
            # data may be list
            if isinstance(data, list) and len(data) > 0:
                return data[0], None
            if isinstance(data, dict):
                return data, None
        return None, "USER_NOT_FOUND"
    except Exception as e:
        logger.warning("[UsernameMapping] Supabase lookup failed: %s", e)
        return None, "USER_NOT_FOUND"


def get_username_by_email(email):
    query_email = email.strip().lower()
    # Local mirror
    try:
        local_path = _local_usernames_path()
        if local_path and os.path.exists(local_path):
            import json
            with open(local_path, "r", encoding="utf-8") as f:
                mappings = json.load(f)
            for uname, data in mappings.items():
                if data.get("email", "").strip().lower() == query_email:
                    return uname
    except Exception as e:
        logger.warning("[UsernameMapping] Local reverse lookup failed: %s", e)

    # Supabase lookup
    try:
        res = supabase_admin.table("usernames").select("username").eq("email", query_email).execute()
        data = getattr(res, 'data', None) or res
        if data:
            if isinstance(data, list) and len(data) > 0:
                return data[0].get("username")
            if isinstance(data, dict):
                return data.get("username")
    except Exception as e:
        logger.warning("[UsernameMapping] Supabase reverse lookup failed: %s", e)

    return None


def update_avatar_in_mapping(username, emoji):
    clean_username = username.strip().lower()
    # Update local mirror
    try:
        local_path = _local_usernames_path()
        if local_path and os.path.exists(local_path):
            import json
            with open(local_path, "r", encoding="utf-8") as f:
                mappings = json.load(f)
            if clean_username in mappings:
                mappings[clean_username]["avatar_emoji"] = emoji
                with open(local_path, "w", encoding="utf-8") as f:
                    json.dump(mappings, f, indent=2)
    except Exception as e:
        logger.warning("[UsernameMapping] Local avatar update failed: %s", e)

    # Update Supabase table
    try:
        res = supabase_admin.table("usernames").update({"avatar_emoji": emoji}).eq("username", clean_username).execute()
        logger.info("[UsernameMapping] Supabase avatar update result: %s", getattr(res, 'data', res))
        return True
    except Exception as e:
        logger.warning("[UsernameMapping] Supabase avatar update failed: %s", e)
        return True
