from fastapi import APIRouter, Depends

from app.deps import get_session
from app.schemas import AssistantRequest, AssistantResponse, ChatMessageResponse
from app.services.assistant_service import handle_assistant_message, reset_assistant_session, get_chat_history_for_session
from app.services.session_store import UserSession

router = APIRouter()


@router.post("/message", response_model=AssistantResponse)
def message(payload: AssistantRequest, session: UserSession = Depends(get_session)):
    return handle_assistant_message(session, payload.message, payload.client_time)


@router.get("/history", response_model=list[ChatMessageResponse])
def get_history(session: UserSession = Depends(get_session)):
    return get_chat_history_for_session(session)


@router.post("/reset")
def reset_assistant(session: UserSession = Depends(get_session)):
    reset_assistant_session(session)
    return {"status": "ok"}

