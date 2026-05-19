import os
import re
import secrets
import json
from dataclasses import dataclass, asdict
from pathlib import Path

from backend.crypto import derive_key, gen_salt, load_salt_for, save_salt_for
from backend.storage import init_db_for


ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "backend_api" / "data"
SESSIONS_FILE = DATA_DIR / "active_sessions.json"
SESSIONS: dict[str, "UserSession"] = {}


@dataclass(frozen=True)
class UserSession:
    session_id: str
    username: str
    email: str
    db_path: str
    key_hex: str  # Store hex for serialization
    id_token: str = ""
    display_name: str = ""
    uid: str = ""
    avatar_emoji: str = ""

    @property
    def key(self) -> bytes:
        return bytes.fromhex(self.key_hex)


def _safe_username(username: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]", "_", username.strip().lower())
    if not cleaned:
        raise ValueError("Username is required")
    return cleaned


def _save_sessions_to_disk():
    try:
        data = {sid: asdict(sess) for sid, sess in SESSIONS.items()}
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"DEBUG: Failed to save sessions to disk: {e}")


def _load_sessions_from_disk():
    if not SESSIONS_FILE.exists():
        return
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for sid, sess_data in data.items():
                SESSIONS[sid] = UserSession(**sess_data)
        print(f"DEBUG: Restored {len(SESSIONS)} sessions from disk.")
    except Exception as e:
        print(f"DEBUG: Failed to load sessions from disk: {e}")


# Initialize sessions on module load
_load_sessions_from_disk()


def create_dev_session(
    username: str,
    email: str,
    secret: str,
    id_token: str = "",
    display_name: str = "",
    uid: str = "",
    avatar_emoji: str = "",
) -> UserSession:
    print(f"DEBUG: Creating session for {username} ({email})")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    safe_username = _safe_username(username)
    
    # Generate a stable UUID for dev sessions to keep Supabase happy
    if not uid:
        import uuid
        uid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"remindme.dev.{safe_username}"))

    salt = load_salt_for(safe_username, path=str(DATA_DIR))
    if salt is None:
        salt = gen_salt()
        save_salt_for(safe_username, salt, path=str(DATA_DIR))

    key = derive_key(f"{safe_username}:{email}:{secret}", salt)
    init_db_for(safe_username, key, path=str(DATA_DIR))

    session_id = secrets.token_urlsafe(32)
    session = UserSession(
        session_id=session_id,
        username=safe_username,
        email=email,
        db_path=os.path.join(str(DATA_DIR), f"tasks_{safe_username}.db"),
        key_hex=key.hex(),
        id_token=id_token,
        display_name=display_name or username,
        uid=uid,
        avatar_emoji=avatar_emoji,
    )
    SESSIONS[session_id] = session
    _save_sessions_to_disk()
    print(f"DEBUG: Session {session_id} saved and persisted.")
    return session


def get_session_by_id(session_id: str) -> UserSession | None:
    if not session_id:
        return None
    sess = SESSIONS.get(session_id)
    if sess:
        print(f"DEBUG: Valid session retrieved for {sess.username}")
    else:
        print(f"DEBUG: Session ID {session_id} not found in store.")
    return sess


def delete_session(session_id: str):
    if session_id in SESSIONS:
        del SESSIONS[session_id]
        _save_sessions_to_disk()
        print(f"DEBUG: Session {session_id} deleted.")


def update_avatar(session_id: str, emoji: str) -> bool:
    session = SESSIONS.get(session_id)
    if not session:
        return False
    
    # UserSession is a frozen dataclass, so we create a new instance
    new_session = UserSession(
        session_id=session.session_id,
        username=session.username,
        email=session.email,
        db_path=session.db_path,
        key_hex=session.key_hex,
        id_token=session.id_token,
        display_name=session.display_name,
        uid=session.uid,
        avatar_emoji=emoji,
    )
    SESSIONS[session_id] = new_session
    _save_sessions_to_disk()
    return True
