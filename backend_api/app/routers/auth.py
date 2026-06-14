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
)
from app.services.session_store import create_dev_session, update_avatar, UserSession
# Auth operations now use Supabase admin/client
from backend.supabase_auth import (
    sign_in_with_email_password,
    sign_up_with_email_password,
    update_password,
    get_user_data,
    resend_verification_email,
)

# Use Supabase-backed username mapping helpers (replace Firebase RTDB)
from backend.supabase_auth import (
    save_username_mapping,
    get_username_data,
    get_username_by_email,
    update_profile,
)
# Use Supabase OTP flow for forgot-password (6-digit code via email service)
from backend.supabase_auth import (
    reset_password_email,
    confirm_password_reset,
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
    
    save_username_mapping(safe_username, payload.email, uid, metadata={"salt_hex": salt.hex(), "passphrase_uid": uid})

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
        user_data = None
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
        
        # Include raw error for debugging/display on client when needed
        raise HTTPException(status_code=401, detail={"message": detail, "raw_error": str(error)})

    uid = data.get("localId")
    id_token = data.get("idToken")
    print(f"DEBUG: Auth success. UID: {uid}")

    # CRITICAL: Find the REAL mapped username instead of guessing from display_name
    # This prevents "Data Gone" issue when display_name changes or email login is used
    mapped_username = get_username_by_email(email)
    print(f"DEBUG: Reverse lookup for {email} returned: {mapped_username}")
    if mapped_username:
        mapped_user_data, mapped_error = get_username_data(mapped_username)
        if mapped_user_data:
            user_data = mapped_user_data
        elif mapped_error:
            print(f"DEBUG: Reverse mapping data lookup failed for {mapped_username}: {mapped_error}")
    
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
    # passphrase_uid: the exact uid used in PBKDF2 key derivation for this user.
    # May differ from Firebase uid for legacy accounts that were created with Supabase UUID.
    cloud_passphrase_uid = cloud_metadata.get("passphrase_uid") if isinstance(cloud_metadata, dict) else None
    
    if cloud_salt_hex:
        if local_salt is None or local_salt.hex() != cloud_salt_hex:
            try:
                restored_salt = bytes.fromhex(cloud_salt_hex)
                save_salt_for(final_username, restored_salt, path=str(DATA_DIR))
                print(f"DEBUG: Restored local salt for {final_username} from cloud metadata (was different or missing).")
            except Exception as e:
                print(f"DEBUG ERROR: Failed to restore local salt: {e}")
    elif local_salt is not None:
        try:
            salt_hex = local_salt.hex()
            save_username_mapping(final_username, email, uid, metadata={"salt_hex": salt_hex, "passphrase_uid": uid})
            print(f"DEBUG: Synced existing local salt for {final_username} to cloud mapping database.")
        except Exception as e:
            print(f"DEBUG ERROR: Failed to sync local salt to cloud: {e}")
    # ─────────────────────────────────────────────────────────────────────────
    
    # Use the stored passphrase_uid if available (ensures correct key derivation
    # for legacy accounts where Supabase UUID != Firebase uid)
    secret_for_key = cloud_passphrase_uid if cloud_passphrase_uid else uid
    print(f"DEBUG: Using passphrase_uid='{secret_for_key[:20]}...' for key derivation (firebase uid='{uid[:20]}...')")
    
    print(f"DEBUG: Creating local encrypted session for {final_username}")
    session = create_dev_session(
        username=final_username,
        email=email,
        secret=secret_for_key,
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
    Send password reset using a 6-digit OTP delivered via the HTTP email service (Resend/Brevo).
    The user receives the OTP code in their email and enters it in the app to reset their password.
    """
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(f"forgot_password_{client_ip}", max_requests=3, window_minutes=15)
    
    auth_logger.info(f"[Forgot Password] Request received for: {payload.username} from IP: {client_ip}")
    
    email = None
    
    if "@" in payload.username:
        email = payload.username.strip().lower()
        auth_logger.info(f"[Forgot Password] Input is email: {email}")
    else:
        auth_logger.info(f"[Forgot Password] Input is username: {payload.username}")
        user_data, error = get_username_data(payload.username)
        if error or not user_data:
            auth_logger.warning(f"[Forgot Password] Username not found: {payload.username}. Error: {error}")
            raise HTTPException(status_code=400, detail="This username is not registered.")
        email = user_data.get("email")
        auth_logger.info(f"[Forgot Password] Resolved username '{payload.username}' -> email: {email}")
    
    auth_logger.info(f"[Forgot Password] Generating 6-digit OTP and sending via email service to: {email}")
    data, error = reset_password_email(email)

    if error:
        auth_logger.error(f"[Forgot Password] OTP email delivery failed: {error}")
        detail = f"Failed to send recovery email: {error}"
        if "not registered" in str(error).lower() or "not found" in str(error).lower():
            detail = "This email/username is not registered."
        # Include raw_error for client display/debugging
        raise HTTPException(
            status_code=400,
            detail={"message": detail, "raw_error": str(error)}
        )

    auth_logger.info(f"[Forgot Password] 6-digit OTP sent successfully to {email}")
    # Return any info from reset_password_email (may include developer_otp in dev)
    return data



@router.post("/firebase/confirm-password-reset", response_model=MessageResponse)
def firebase_confirm_password_reset(payload: ConfirmPasswordResetRequest, request: Request):
    """Confirm password reset using the 6-digit OTP code and set a new password via Supabase admin."""
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(f"confirm_reset_{client_ip}", max_requests=5, window_minutes=15)
    
    reset_identity = (payload.email or "").strip()
    if not reset_identity:
        raise HTTPException(status_code=400, detail="Email or username is required.")

    if "@" in reset_identity:
        email = reset_identity.lower()
    else:
        user_data, error = get_username_data(reset_identity)
        if error or not user_data:
            raise HTTPException(status_code=400, detail="Username not found.")
        email = user_data.get("email")

    data, error = confirm_password_reset(payload.reset_code, payload.new_password, email=email)
    if error:
        detail = f"Reset failed: {error}"
        if "expired" in str(error).lower() or "invalid" in str(error).lower():
            detail = "Invalid or expired recovery code. Please request a new one."
        elif "weak" in str(error).lower() or "8 character" in str(error).lower():
            detail = "Password must be at least 8 characters."
        raise HTTPException(status_code=400, detail={"message": detail, "raw_error": str(error)})
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
    from backend.supabase_auth import update_avatar_in_mapping

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
