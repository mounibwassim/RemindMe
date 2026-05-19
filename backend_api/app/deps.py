from fastapi import Header, HTTPException, status

from app.services.session_store import get_session_by_id


def get_session(x_session_id: str = Header(default="")):
    session = get_session_by_id(x_session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-Session-Id header",
        )
    return session
