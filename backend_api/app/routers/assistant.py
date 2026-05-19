from fastapi import APIRouter, Depends

from app.deps import get_session
from app.schemas import AssistantRequest, AssistantResponse
from app.services.assistant_service import handle_assistant_message, reset_assistant_session
from app.services.session_store import UserSession

router = APIRouter()


@router.post("/message", response_model=AssistantResponse)
def message(payload: AssistantRequest, session: UserSession = Depends(get_session)):
    return handle_assistant_message(session, payload.message, payload.client_time)


@router.post("/reset")
def reset_assistant(session: UserSession = Depends(get_session)):
    reset_assistant_session(session)
    return {"status": "ok"}
