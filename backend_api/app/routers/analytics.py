from fastapi import APIRouter, Depends, status, Request

from app.deps import get_session
from app.schemas import AnalyticsSummaryResponse, AuditLogResponse, MessageResponse
from app.services.analytics_service import (
    clear_all_audit_logs_for_session,
    delete_audit_log_for_session,
    get_analytics_summary,
    get_recent_audit_logs,
    reset_analytics_for_session,
)
from app.services.session_store import UserSession

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def summary(request: Request, session: UserSession = Depends(get_session), period: str = "week"):
    tz_offset_min = 0
    try:
        tz_offset_header = request.headers.get("x-timezone-offset")
        if tz_offset_header:
            tz_offset_min = int(tz_offset_header)
    except Exception:
        pass
    return get_analytics_summary(session, period=period, tz_offset_min=tz_offset_min)


@router.get("/audit", response_model=list[AuditLogResponse])
def audit_logs(request: Request, session: UserSession = Depends(get_session), period: str = "week", limit: int = 200):
    tz_offset_min = 0
    try:
        tz_offset_header = request.headers.get("x-timezone-offset")
        if tz_offset_header:
            tz_offset_min = int(tz_offset_header)
    except Exception:
        pass
    return get_recent_audit_logs(session, period=period, limit=limit, tz_offset_min=tz_offset_min)


@router.delete("/audit/{log_id}", response_model=MessageResponse)
def delete_log(log_id: int, session: UserSession = Depends(get_session)):
    delete_audit_log_for_session(session, log_id)
    return MessageResponse(message="Log entry deleted")


@router.delete("/audit", response_model=MessageResponse)
def clear_logs(session: UserSession = Depends(get_session)):
    clear_all_audit_logs_for_session(session)
    return MessageResponse(message="All audit logs cleared")


@router.post("/reset", response_model=MessageResponse)
def reset_analytics(session: UserSession = Depends(get_session)):
    reset_analytics_for_session(session)
    return MessageResponse(message="Analytics and audit logs reset")
