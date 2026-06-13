from datetime import datetime, timedelta, date, timezone

from app.schemas import AnalyticsSummaryResponse, AuditLogResponse
from app.services.insights_service import InsightsService
from app.services.session_store import UserSession
from app.services.task_service import list_tasks_for_session
import backend.supabase_service as supabase


def get_analytics_summary(session: UserSession, period: str = "week") -> AnalyticsSummaryResponse:
    task_models = list_tasks_for_session(session)
    ai_insight = InsightsService.generate_insights(task_models)

    total = len(task_models)
    now_utc = datetime.now(timezone.utc)
    
    pending_tasks = []
    upcoming_tasks = []
    missed_tasks = []
    
    for task in task_models:
        if task.status == "completed" or task.completed_iso:
            continue
            
        due_dt = None
        if task.due_iso:
            try:
                clean_iso = task.due_iso.replace('Z', '+00:00')
                due_dt = datetime.fromisoformat(clean_iso)
                # If naive, assume UTC as per our standard
                if due_dt.tzinfo is None:
                    due_dt = due_dt.replace(tzinfo=timezone.utc)
            except:
                pass
        
        if due_dt:
            if due_dt <= now_utc:
                pending_tasks.append(task)
            else:
                upcoming_tasks.append(task)
                
        if task.is_overdue == 1:
            missed_tasks.append(task)

    completed_count = len([t for t in task_models if t.status == "completed" or t.completed_iso])
    pending = len(pending_tasks)
    upcoming = len(upcoming_tasks)
    missed = len(missed_tasks)

    # Weekly distribution (Last 7 days)
    weekly = _get_weekly_distribution_in_memory(task_models)

    # Audit stats (From Supabase logs)
    # We fetch a larger batch to calculate stats (Increased to 1000 to ensure we catch all notifications)
    raw_logs = supabase.get_audit_logs(session.uid, limit=1000)
    
    audit = {
        "notifications_sent": 0,
        "notification_opened": 0,
        "notification_scheduled": 0,
        "notification_tests": 0,
        "snoozed_events": 0,
        "completed_tasks": 0,
        "created_tasks": 0,
        "edited_tasks": 0,
        "missed_tasks": missed,
        "total_actions": 0,
        "avg_response_min": 0.0,
    }

    task_notified_times = {}
    response_times = []

    # Weekly/Monthly Stats
    today_dt = datetime.now()
    if period == "month":
        start_date = today_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
        if today_dt.month == 12:
            end_date = date(today_dt.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today_dt.year, today_dt.month + 1, 1) - timedelta(days=1)
    else:
        # Default to week
        monday = (today_dt - timedelta(days=today_dt.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = monday.date()
        end_date = (monday + timedelta(days=6)).date()

    def _date_in_period(ts_str: str) -> bool:
        if not ts_str: return False
        try:
            # Parse as UTC and convert to local server timezone
            clean_iso = ts_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_iso)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            local_dt = dt.astimezone()
            return start_date <= local_dt.date() <= end_date
        except Exception as e:
            print(f"Error parsing date {ts_str}: {e}")
            return False

    for log in reversed(raw_logs): 
        action = log.get("action", "")
        tid = log.get("task_id")
        created_at = log.get("created_at", "")
        
        try:
            ts = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except:
            continue

        # Only count events from this period as requested
        if not _date_in_period(created_at):
            continue

        if action in ["notification_notified", "notification_triggered", "notification_sent", "notification_notification_triggered"]:
            audit["notifications_sent"] += 1
            if tid: task_notified_times[tid] = ts
        elif action == "notification_opened":
            audit["notification_opened"] += 1
            if tid in task_notified_times:
                start = task_notified_times.pop(tid)
                diff = (ts - start).total_seconds() / 60.0
                if diff >= 0:
                    response_times.append(diff)
        elif action == "notification_scheduled":
            audit["notification_scheduled"] += 1
        elif action == "notification_test":
            audit["notification_tests"] += 1
        elif action == "task_snoozed":
            audit["snoozed_events"] += 1
        elif action == "task_created":
            audit["created_tasks"] += 1
        elif action == "task_edited":
            audit["edited_tasks"] += 1
        elif action == "task_completed":
            audit["completed_tasks"] += 1

    if response_times:
        audit["avg_response_min"] = round(sum(response_times) / len(response_times), 1)

    audit["total_actions"] = (
        audit.get("notifications_sent", 0) + 
        audit.get("notification_opened", 0) + 
        audit.get("snoozed_events", 0) + 
        audit.get("completed_tasks", 0) +
        audit.get("edited_tasks", 0) +
        audit.get("created_tasks", 0)
    )

    completion_rate = round((completed_count / total) * 100, 1) if total else 0.0
    audit["completion_rate"] = completion_rate

    # Calculate actual completions and creations directly from tasks, 
    # not from audit logs which might truncate.
    completed_period = 0
    created_period = 0
    for task in task_models:
        if task.created_iso and _date_in_period(task.created_iso):
            created_period += 1
        if task.completed_iso and _date_in_period(task.completed_iso):
            completed_period += 1

    snoozed_period = audit["snoozed_events"]
    
    return AnalyticsSummaryResponse(
        total_tasks=total,
        completed=completed_count,
        pending=pending,
        upcoming=upcoming,
        weekly_labels=weekly["labels"],
        weekly_counts=weekly["counts"],
        weekly_range=weekly["range"],
        audit=audit,
        completion_rate=completion_rate,
        ai_insight=ai_insight,
        completed_this_week=completed_period,
        snoozed_this_week=snoozed_period,
        created_this_week=created_period,
    )


def _get_weekly_distribution_in_memory(tasks: list) -> dict:
    today = date.today()
    # Find the most recent Monday
    monday = today - timedelta(days=today.weekday())
    labels = []
    counts = [0] * 7
    days = []
    for i in range(7):
        d = monday + timedelta(days=i)
        days.append(d)
        labels.append(d.strftime("%a"))

    for task in tasks:
        if task.completed_iso:
            try:
                # task.completed_iso might be '2026-05-14T...' or '2026-05-14 ...'
                ts = task.completed_iso.split("T")[0].split(" ")[0]
                comp_dt = date.fromisoformat(ts)
                if comp_dt in days:
                    idx = days.index(comp_dt)
                    counts[idx] += 1
            except Exception:
                continue
    
    # Explicit start/end to avoid off-by-one or timezone display differences
    start_date = days[0]
    end_date = days[0] + timedelta(days=6)
    start_str = start_date.strftime("%d %b %Y")
    end_str = end_date.strftime("%d %b %Y")
    
    return {
        "labels": labels,
        "counts": counts,
        "range": f"{start_str} - {end_str}"
    }


def get_recent_audit_logs(session: UserSession, period: str = "week", limit: int = 200) -> list[AuditLogResponse]:
    # ── Auto Cleanup Old Weeks ──────────────────────────────────────
    try:
        today_dt = datetime.now()
        monday = (today_dt - timedelta(days=today_dt.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        monday_utc = monday.astimezone(timezone.utc)
        monday_utc_iso = monday_utc.isoformat()
        
        # Delete from Supabase table
        supabase.supabase.table("audit_logs").delete().eq("user_id", session.uid).lt("created_at", monday_utc_iso).execute()
        print(f"DEBUG: Cleaned up old audit logs older than {monday_utc_iso}")
    except Exception as e:
        print(f"Error during auto-cleanup of old audit logs: {e}")

    try:
        rows = supabase.get_audit_logs(session.uid, limit=limit)
        logs: list[AuditLogResponse] = []
        
        today_dt = datetime.now()
        monday = (today_dt - timedelta(days=today_dt.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        first_of_month = today_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        monday_utc = monday.astimezone(timezone.utc)
        first_of_month_utc = first_of_month.astimezone(timezone.utc)
        
        for row in rows:
            created_at = row.get("created_at", "")
            try:
                ts = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            except:
                continue
                
            if period == "week":
                if ts < monday_utc:
                    continue
            elif period == "month":
                if ts < first_of_month_utc:
                    continue
                    
            logs.append(
                AuditLogResponse(
                    id=row.get("id"),
                    task_id=None, # Supabase logs don't always have task_id linked directly in same schema
                    event=row.get("action", ""),
                    timestamp_iso=created_at,
                    user_uid=row.get("user_id", ""),
                    extra=row.get("details", ""),
                    notification_scheduled_at=row.get("notification_scheduled_at"),
                    notification_sent_at=row.get("notification_sent_at"),
                )
            )
        return logs
    except Exception as e:
        print(f"Error fetching audit logs: {e}")
        return []


def _count_audit_event(session: UserSession, event: str) -> int:
    # This is inefficient, but keeps compatibility if needed. 
    # Better to use the counts calculated in get_analytics_summary.
    try:
        logs = supabase.get_audit_logs(session.uid, limit=500)
        return sum(1 for log in logs if log.get("action") == event)
    except Exception:
        return 0


def delete_audit_log_for_session(session: UserSession, log_id: int):
    try:
        # Delete the specific audit log for this user
        supabase.supabase.table("audit_logs").delete().eq("id", log_id).eq("user_id", session.uid).execute()
    except Exception as e:
        print(f"Error deleting audit log {log_id} for {session.uid}: {e}")
        return


def clear_all_audit_logs_for_session(session: UserSession):
    try:
        # Delete all audit logs for this user
        supabase.supabase.table("audit_logs").delete().eq("user_id", session.uid).execute()
    except Exception as e:
        print(f"Error clearing audit logs for {session.uid}: {e}")
        return


def reset_analytics_for_session(session: UserSession):
    """Reset analytics and audit logs for a user.

    This removes the analytics row and clears audit logs so frontend
    statistics (notifications, counts) become zero.
    """
    try:
        # Delete analytics entry from Supabase
        try:
            supabase.delete_analytics(session.uid)
        except Exception as e:
            print(f"Error deleting analytics row for {session.uid}: {e}")

        # Clear audit logs
        clear_all_audit_logs_for_session(session)
    except Exception as e:
        print(f"Error resetting analytics for {session.uid}: {e}")
        return

