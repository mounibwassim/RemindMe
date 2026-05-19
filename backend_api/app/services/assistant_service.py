from backend.ai_assistant import handle_user_input, reset_task_state

from app.schemas import AssistantResponse, TaskCreateRequest
from app.services.session_store import UserSession
from app.services.task_service import create_task_for_session


_drafts: dict[str, dict] = {}


def handle_assistant_message(session: UserSession, message: str, client_time: str = None) -> AssistantResponse:
    draft = _drafts.get(session.session_id)
    draft_copy = draft.copy() if isinstance(draft, dict) else None
    result = handle_user_input(message, client_time=client_time, _draft_ext=draft_copy)
    
    res_type = result.get("type", "chat")
    res_text = result.get("response", "")
    res_task = result.get("task", {})

    # Intercept auto-persistence confirmation
    if res_type == "ready_to_save":
        title = res_task.get("title", "")
        date_str = res_task.get("date", "")
        time_str = res_task.get("time", "")
        p_str = res_task.get("priority", "Medium")
        category = res_task.get("category", "General")
        
        p_map = {"high": 1, "medium": 2, "low": 3}
        priority_int = p_map.get(p_str.lower(), 3)
        
        try:
            due_iso = f"{date_str}T{time_str}:00"
            create_task_for_session(
                session,
                TaskCreateRequest(
                    title=title,
                    due_iso=due_iso,
                    priority=priority_int,
                    category=category,
                ),
            )
            res_type = "created"
            res_text = f"Task successfully created and saved to your database! ✅\n'{title}' scheduled for {date_str} at {time_str}."
            res_task = {"title": "", "date": "", "time": "", "priority": "Medium", "category": "General"}
        except Exception as e:
            res_type = "chat"
            res_text = f"Failed to save task to database: {e}"

    _drafts[session.session_id] = res_task
    return AssistantResponse(
        type=res_type,
        response=res_text,
        task=res_task,
    )


def reset_assistant_session(session: UserSession):
    _drafts.pop(session.session_id, None)
    reset_task_state()

