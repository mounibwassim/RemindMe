from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import get_session
from app.schemas import (
    MessageResponse,
    NotificationEventRequest,
    SnoozeTaskRequest,
    TaskCreateRequest,
    TaskResponse,
    TaskUpdateRequest,
)
from app.services.session_store import UserSession
from app.services.task_service import (
    complete_task_for_session,
    create_task_for_session,
    delete_all_tasks_for_session,
    delete_task_for_session,
    list_tasks_for_session,
    log_notification_event_for_session,
    reopen_task_for_session,
    snooze_task_for_session,
    update_task_for_session,
)

router = APIRouter()


@router.get("", response_model=list[TaskResponse])
def list_tasks(session: UserSession = Depends(get_session)):
    return list_tasks_for_session(session)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreateRequest, session: UserSession = Depends(get_session)):
    return create_task_for_session(session, payload)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    payload: TaskUpdateRequest,
    session: UserSession = Depends(get_session),
):
    task = update_task_for_session(session, task_id, payload)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/complete", response_model=MessageResponse)
def complete_task(task_id: str, session: UserSession = Depends(get_session)):
    complete_task_for_session(session, task_id, datetime.now().isoformat())
    return MessageResponse(message="Task completed")


@router.post("/{task_id}/reopen", response_model=MessageResponse)
def reopen_task(task_id: str, session: UserSession = Depends(get_session)):
    reopen_task_for_session(session, task_id)
    return MessageResponse(message="Task reopened")


@router.post("/{task_id}/snooze", response_model=MessageResponse)
def snooze_task(
    task_id: str,
    payload: SnoozeTaskRequest,
    session: UserSession = Depends(get_session),
):
    snooze_task_for_session(session, task_id, payload.minutes)
    return MessageResponse(message="Task snoozed")


@router.delete("/all", response_model=MessageResponse)
def delete_all_tasks(session: UserSession = Depends(get_session)):
    delete_all_tasks_for_session(session)
    return MessageResponse(message="All tasks cleared")

@router.delete("/{task_id}", response_model=MessageResponse)
def delete_task(task_id: str, session: UserSession = Depends(get_session)):
    delete_task_for_session(session, task_id)
    return MessageResponse(message="Task deleted")


@router.post("/{task_id}/notification-event", response_model=MessageResponse)
def notification_event(
    task_id: str,
    payload: NotificationEventRequest,
    session: UserSession = Depends(get_session),
):
    logged = log_notification_event_for_session(
        session,
        task_id,
        payload.event,
        extra=payload.extra,
    )
    return MessageResponse(
        message="Notification event logged" if logged else "Notification event already current"
    )
