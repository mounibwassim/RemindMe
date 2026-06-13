from fastapi import APIRouter, Depends, HTTPException, status, Request
import logging
import os

# Setup auth router logger
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
auth_log_path = os.path.join(project_root, "auth_debug.log")
auth_logger = logging.getLogger("auth_router")
if not auth_logger.handlers:
    auth_logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(auth_log_path)
    fh.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fh.setFormatter(fmt)
    auth_logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(fmt)
    auth_logger.addHandler(ch)

from app.deps import get_session
from app.schemas import (
    ChangePasswordRequest,
    ConfirmPasswordResetRequest,
    DevLoginRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    SessionResponse,
    AuthSessionResponse,
    AvatarUpdateRequest,
    ForgotPasswordRequest, 
)
from app.services.session_store import create_dev_session, update_avatar, UserSession
from backend.supabase_auth import (
    sign_in_with_email_password,
    sign_up_with_email_password,
    reset_password_email,
    update_password,
    get_user_data,
    confirm_password_reset,
    resend_verification_email,
    supabase_admin,
)
from backend.firebase_service import (
    save_username_mapping,
    get_username_data,
    get_username_by_email,
    update_profile,
)

router = APIRouter()


@router.post("/dev-login", response_model=SessionResponse)
def dev_login(payload: DevLoginRequest):
    """Local dev session using encryption secret (backward-compatible)."""
    session = create_dev_session(
        username=payload.username,
        email=payload.email,
        secret=payload.secret,
    )
    return SessionResponse(
        session_id=session.session_id,
        username=session.username,
        email=session.email,
    )


@router.post("/firebase/signup", response_model=AuthSessionResponse)
def firebase_signup(payload: RegisterRequest):
    """Firebase sign-up with automatic encrypted session creation."""
    safe_username = _safe_name(payload.display_name)
    existing_user, _ = get_username_data(safe_username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username is already taken. Please choose another one.")
        
    data, error = sign_up_with_email_password(payload.email, payload.password)
    if error:
        detail = f"Signup failed: {error}"
        error_str = str(error).lower()
        if "user_already_exists" in error_str or "already registered" in error_str:
            detail = "This email is already registered. Please Sign In instead."
        elif "weak_password" in error_str:
            detail = "Password is too weak. Please use at least 8 characters."
        raise HTTPException(status_code=400, detail=detail)

    uid = data.get("localId")
    id_token = data.get("idToken") or ""  # Ensure it's a string, not None

    safe_username = _safe_name(payload.display_name)
    # Generate/save salt first so we can store it in the cloud mapping database
    update_profile(id_token, safe_username)
    from backend.crypto import load_salt_for, save_salt_for, gen_salt
    from backend_api.app.services.session_store import DATA_DIR
    salt = load_salt_for(safe_username, path=str(DATA_DIR))
    if salt is None:
        salt = gen_salt()
        save_salt_for(safe_username, salt, path=str(DATA_DIR))
    
    save_username_mapping(safe_username, payload.email, uid, metadata={"salt_hex": salt.hex()})

    session = create_dev_session(
        username=safe_username,
        email=payload.email,
        secret=uid,
        id_token=id_token,
        display_name=payload.display_name,
        uid=uid,
    )
    return AuthSessionResponse(
        session_id=session.session_id,
        username=safe_username,
        display_name=payload.display_name,
        email=payload.email,
        uid=uid,
        avatar_emoji=session.avatar_emoji,
    )


@router.post("/firebase/signin", response_model=AuthSessionResponse)
def firebase_signin(payload: LoginRequest, request: Request):
    """Firebase sign-in with Username -> Email lookup."""
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(f"login_{client_ip}", max_requests=10, window_minutes=15)

    print(f"DEBUG: Login attempt for username/email: {payload.username}")
    
    if "@" in payload.username:
        email = payload.username.strip().lower()
        display_name_hint = email.split("@", 1)[0]
        print(f"DEBUG: Direct email login detected: {email}")
    else:
        print(f"DEBUG: Username lookup required for: {payload.username}")
        user_data, error = get_username_data(payload.username)
        if error or not user_data:
            print(f"DEBUG: Username mapping NOT found for {payload.username}. Error: {error}")
            raise HTTPException(
                status_code=401,
                detail="Username mapping not found. Please sign in using your registered Email address, or sign up again.",
            )
        email = user_data.get("email")
        display_name_hint = payload.username
        print(f"DEBUG: Mapped {payload.username} to {email}")

    print(f"DEBUG: Calling Supabase sign_in_with_email_password for {email}")
    data, error = sign_in_with_email_password(email, payload.password)

    if error:
        print(f"DEBUG: Supabase auth error: {error}")
        detail = "Incorrect password"
        error_str = str(error).lower()
        if "invalid login credentials" in error_str:
            detail = "Incorrect password. If you haven't created a cloud account yet, please Sign Up first."
        elif "email not confirmed" in error_str:
            detail = "Please confirm your email address before signing in."
        elif "user not found" in error_str:
            detail = "Account not found. Please Sign Up to create your RemindMe cloud account."
        elif "too many requests" in error_str:
            detail = "Too many login attempts. Please try again later."
        else:
            # Pass through the error if it's something else
            detail = f"Login failed: {error}"
        
        raise HTTPException(status_code=401, detail=detail)

    uid = data.get("localId")
    id_token = data.get("idToken")
    print(f"DEBUG: Auth success. UID: {uid}")

    # CRITICAL: Find the REAL mapped username instead of guessing from display_name
    # This prevents "Data Gone" issue when display_name changes or email login is used
    mapped_username = get_username_by_email(email)
    print(f"DEBUG: Reverse lookup for {email} returned: {mapped_username}")
    
    user_info = get_user_data(id_token)
    display_name = (
        user_info.get("displayName")
        if user_info and user_info.get("displayName")
        else display_name_hint
    )
    
    # Use mapped username if found, otherwise fallback to safe display_name
    final_username = mapped_username if mapped_username else _safe_name(display_name)
    print(f"DEBUG: Final session username: {final_username}")

    # Retrieve avatar from mapping if it exists
    avatar_emoji = user_data.get("avatar_emoji", "") if user_data else ""

    # ── Salt Sync & Restoration ──────────────────────────────────────────────
    from backend.crypto import load_salt_for, save_salt_for
    from backend_api.app.services.session_store import DATA_DIR
    
    local_salt = load_salt_for(final_username, path=str(DATA_DIR))
    cloud_metadata = user_data.get("metadata") if user_data else None
    cloud_salt_hex = cloud_metadata.get("salt_hex") if isinstance(cloud_metadata, dict) else None
    
    if cloud_salt_hex:
        if local_salt is None:
            try:
                restored_salt = bytes.fromhex(cloud_salt_hex)
                save_salt_for(final_username, restored_salt, path=str(DATA_DIR))
                print(f"DEBUG: Restored local salt for {final_username} from cloud metadata.")
            except Exception as e:
                print(f"DEBUG ERROR: Failed to restore local salt: {e}")
    elif local_salt is not None:
        try:
            salt_hex = local_salt.hex()
            save_username_mapping(final_username, email, uid, metadata={"salt_hex": salt_hex})
            print(f"DEBUG: Synced existing local salt for {final_username} to cloud mapping database.")
        except Exception as e:
            print(f"DEBUG ERROR: Failed to sync local salt to cloud: {e}")
    # ─────────────────────────────────────────────────────────────────────────
    
    print(f"DEBUG: Creating local encrypted session for {final_username}")
    session = create_dev_session(
        username=final_username,
        email=email,
        secret=uid,
        id_token=id_token,
        display_name=display_name,
        uid=uid,
        avatar_emoji=avatar_emoji,
    )
    print(f"DEBUG: Session created. ID: {session.session_id}")
    
    return AuthSessionResponse(
        session_id=session.session_id,
        username=final_username,
        display_name=display_name,
        email=email,
        uid=uid,
        avatar_emoji=session.avatar_emoji,
    )


from fastapi import Request
from app.security import check_rate_limit
import time

@router.post("/firebase/forgot-password")
def firebase_forgot_password(payload: ForgotPasswordRequest, request: Request):
    """
    Supabase password recovery flow.
    """
    client_ip = request.client.host if request.client else "unknown"
    # Rate limit: max 3 requests per 15 mins per IP
    check_rate_limit(f"forgot_password_{client_ip}", max_requests=3, window_minutes=15)
    
    auth_logger.info(f"[Forgot Password] Request received for: {payload.username} from IP: {client_ip}")
    
    email = None
    
    if "@" in payload.username:
        email = payload.username.strip().lower()
        auth_logger.info(f"[Forgot Password] Input is an email. Checking existence of: {email}")
        user_res = supabase_admin.auth.admin.list_users()
        user = next((u for u in user_res if u.email == email), None)
        if not user:
            auth_logger.warning(f"[Forgot Password] Email not registered: {email}")
            raise HTTPException(status_code=400, detail="This email is not registered.")
        auth_logger.info(f"[Forgot Password] Registered user found for email: {email} (UID: {user.id})")
    else:
        auth_logger.info(f"[Forgot Password] Input is a username. Resolving username: {payload.username}")
        user_data, error = get_username_data(payload.username)
        if error or not user_data:
            auth_logger.warning(f"[Forgot Password] Username not registered: {payload.username}. Error: {error}")
            raise HTTPException(status_code=400, detail="This username is not registered.")
        email = user_data.get("email")
        auth_logger.info(f"[Forgot Password] Mapped username {payload.username} to email: {email}")
    
    auth_logger.info(f"[Forgot Password] Triggering OTP generation and email send to: {email}")
    data, error = reset_password_email(email)
    
    if error:
        auth_logger.error(f"[Forgot Password] OTP Generation or system error: {error}")
        raise HTTPException(status_code=400, detail=f"Failed to generate OTP or send email: {error}")
        
    if data and data.get("message") == "OTP_GENERATED_BUT_EMAIL_FAILED":
        err_msg = data.get("error") or "SMTP connection timeout"
        auth_logger.error(f"[Forgot Password] OTP generated but email failed to send: {err_msg}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to send recovery email. SMTP error: {err_msg}. Please verify configuration."
        )
        
    auth_logger.info(f"[Forgot Password] Success! Recovery email successfully sent to {email}")
    return {"message": "Recovery email sent successfully."}


@router.post("/firebase/confirm-password-reset", response_model=MessageResponse)
def firebase_confirm_password_reset(payload: ConfirmPasswordResetRequest, request: Request):
    """Confirm Firebase password reset with the token from the reset email."""
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(f"confirm_reset_{client_ip}", max_requests=5, window_minutes=15)
    
    if "@" in payload.email:
        email = payload.email.strip().lower()
    else:
        user_data, error = get_username_data(payload.email)
        if error or not user_data:
            raise HTTPException(status_code=400, detail="Username not found.")
        email = user_data.get("email")

    data, error = confirm_password_reset(payload.reset_code, payload.new_password, email=email)
    if error:
        detail = f"Reset failed: {error}"
        if "Invalid or expired reset token" in str(error):
            detail = "Invalid or expired reset token."
        elif "WEAK_PASSWORD" in str(error):
            detail = "Password must be at least 8 characters."
        raise HTTPException(status_code=400, detail=detail)
    return MessageResponse(
        message="Password reset successfully. You can sign in with your new password."
    )


@router.post("/resend-verification", response_model=MessageResponse)
def resend_verification(payload: ForgotPasswordRequest):
    """Resend signup verification email."""
    # We reuse ForgotPasswordRequest because it just contains 'username' (which can be email)
    if "@" in payload.username:
        email = payload.username.strip().lower()
    else:
        user_data, error = get_username_data(payload.username)
        if error or not user_data:
            raise HTTPException(status_code=400, detail="Username not found.")
        email = user_data.get("email")

    data, error = resend_verification_email(email)
    if error:
        raise HTTPException(status_code=400, detail=f"Resend failed: {error}")
    return MessageResponse(message=f"Verification email resent to {email}.")


@router.post("/firebase/change-password", response_model=MessageResponse)
def firebase_change_password(
    payload: ChangePasswordRequest,
    session: UserSession = Depends(get_session),
):
    """Change Firebase password for authenticated session with verification."""
    if not session.id_token or not session.email:
        raise HTTPException(
            status_code=401,
            detail="Firebase session not available. Please sign in again.",
        )
    
    # STEP 1: Verify current password and get fresh token
    fresh_data, error = sign_in_with_email_password(session.email, payload.current_password)
    if error:
        raise HTTPException(status_code=401, detail="Current password incorrect.")

    # STEP 2: Update to new password using the fresh token
    fresh_id_token = fresh_data.get("idToken")
    data, error = update_password(fresh_id_token, payload.new_password)
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return MessageResponse(message="Password changed successfully.")


@router.patch("/avatar", response_model=MessageResponse)
def patch_avatar(
    payload: AvatarUpdateRequest,
    session: UserSession = Depends(get_session),
):
    """Update user's avatar emoji and persist it."""
    from backend.firebase_service import update_avatar_in_mapping
    
    success = update_avatar(session.session_id, payload.avatar_emoji)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update session avatar.")
        
    # Persist to mapping (Firebase)
    update_avatar_in_mapping(session.username, payload.avatar_emoji)
    
    return MessageResponse(message="Avatar updated successfully.")


def _safe_name(name: str) -> str:
    import re
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]", "_", name.strip().lower())
    return cleaned if cleaned else "user"
