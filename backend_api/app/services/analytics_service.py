from datetime import datetime, timedelta, date, timezone
import json

from app.schemas import AnalyticsSummaryResponse, AuditLogResponse
from app.services.insights_service import InsightsService
from app.services.session_store import UserSession
from app.services.task_service import list_tasks_for_session
import backend.supabase_service as supabase


def get_analytics_summary(session: UserSession, period: str = "week", tz_offset_min: int = 0) -> AnalyticsSummaryResponse:
    task_models = list_tasks_for_session(session)
    ai_insight = InsightsService.generate_insights(task_models)

    total = len(task_models)
    now_utc = datetime.now(timezone.utc)
    user_local_time = now_utc + timedelta(minutes=tz_offset_min)
    user_today = user_local_time.date()
    
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

    # Calculate both weekly and monthly distributions
    weekly = _get_weekly_distribution_in_memory(task_models, tz_offset_min=tz_offset_min)
    monthly = _get_monthly_distribution_in_memory(task_models, tz_offset_min=tz_offset_min)

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
        "reset_events": 0,
        "missed_tasks": missed,
        "total_actions": 0,
        "avg_response_min": 0.0,
    }

    task_notified_times = {}
    response_times = []
    missed_count = 0

    # Weekly/Monthly Stats
    if period == "month":
        start_date = user_today.replace(day=1)
        if user_today.month == 12:
            end_date = date(user_today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(user_today.year, user_today.month + 1, 1) - timedelta(days=1)
    else:
        # Default to week
        monday = user_today - timedelta(days=user_today.weekday())
        start_date = monday
        end_date = monday + timedelta(days=6)

    def _date_in_period(ts_str: str) -> bool:
        if not ts_str: return False
        try:
            # Parse as UTC and convert to client local timezone
            clean_iso = ts_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_iso)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            client_dt = dt + timedelta(minutes=tz_offset_min)
            return start_date <= client_dt.date() <= end_date
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
        elif action in ["task_snoozed", "notification_snoozed_from_notification", "snoozed_from_notification"]:
            audit["snoozed_events"] += 1
        elif action == "task_created":
            audit["created_tasks"] += 1
        elif action == "task_edited":
            audit["edited_tasks"] += 1
        elif action in ["task_completed", "notification_completed_from_notification", "completed_from_notification"]:
            audit["completed_tasks"] += 1
        elif action in ["system_reset", "logs_cleared", "all_tasks_cleared"]:
            audit["reset_events"] += 1
        elif action in ["notification_missed", "reminder_missed", "notification_reminder_missed", "missed"]:
            missed_count += 1

    if response_times:
        audit["avg_response_min"] = round(sum(response_times) / len(response_times), 1)

    audit["missed_tasks"] = missed_count if missed_count > 0 else missed

    audit["total_actions"] = (
        audit.get("notifications_sent", 0) + 
        audit.get("notification_opened", 0) + 
        audit.get("snoozed_events", 0) + 
        audit.get("completed_tasks", 0) +
        audit.get("edited_tasks", 0) +
        audit.get("created_tasks", 0) +
        audit.get("reset_events", 0)
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
        monthly_labels=monthly["labels"],
        monthly_counts=monthly["counts"],
        monthly_range=monthly["range"],
        audit=audit,
        completion_rate=completion_rate,
        ai_insight=ai_insight,
        completed_this_week=completed_period,
        snoozed_this_week=snoozed_period,
        created_this_week=created_period,
    )


def _get_weekly_distribution_in_memory(tasks: list, tz_offset_min: int = 0) -> dict:
    now_utc = datetime.now(timezone.utc)
    user_local_time = now_utc + timedelta(minutes=tz_offset_min)
    user_today = user_local_time.date()
    
    # Find the most recent Monday based on client local date
    monday = user_today - timedelta(days=user_today.weekday())
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
                # Convert task.completed_iso to client local timezone date
                clean_iso = task.completed_iso.replace("Z", "+00:00")
                comp_dt_utc = datetime.fromisoformat(clean_iso)
                if comp_dt_utc.tzinfo is None:
                    comp_dt_utc = comp_dt_utc.replace(tzinfo=timezone.utc)
                comp_dt_local = comp_dt_utc + timedelta(minutes=tz_offset_min)
                comp_dt = comp_dt_local.date()
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


def _get_monthly_distribution_in_memory(tasks: list, tz_offset_min: int = 0) -> dict:
    now_utc = datetime.now(timezone.utc)
    user_local_time = now_utc + timedelta(minutes=tz_offset_min)
    user_today = user_local_time.date()
    
    # Weeks of the current month
    labels = ["W1", "W2", "W3", "W4"]
    counts = [0] * 4
    
    # Check if the month has a 5th week (day 29+)
    year = user_today.year
    month = user_today.month
    if month == 12:
        last_day = (date(year + 1, 1, 1) - timedelta(days=1)).day
    else:
        last_day = (date(year, month + 1, 1) - timedelta(days=1)).day
        
    if last_day > 28:
        labels.append("W5")
        counts.append(0)
        
    for task in tasks:
        if task.completed_iso:
            try:
                clean_iso = task.completed_iso.replace("Z", "+00:00")
                comp_dt_utc = datetime.fromisoformat(clean_iso)
                if comp_dt_utc.tzinfo is None:
                    comp_dt_utc = comp_dt_utc.replace(tzinfo=timezone.utc)
                comp_dt_local = comp_dt_utc + timedelta(minutes=tz_offset_min)
                comp_dt = comp_dt_local.date()
                
                if comp_dt.year == year and comp_dt.month == month:
                    day = comp_dt.day
                    if day <= 7:
                        counts[0] += 1
                    elif day <= 14:
                        counts[1] += 1
                    elif day <= 21:
                        counts[2] += 1
                    elif day <= 28:
                        counts[3] += 1
                    else:
                        counts[4] += 1
            except Exception:
                continue
                
    month_name = user_today.strftime("%B %Y")
    return {
        "labels": labels,
        "counts": counts,
        "range": f"01 - {last_day:02d} {month_name}"
    }


def get_recent_audit_logs(session: UserSession, period: str = "week", limit: int = 200, tz_offset_min: int = 0) -> list[AuditLogResponse]:
    # ── Auto Cleanup Old Audit Logs (60 days) ──────────────────────────────────
    try:
        today_dt = datetime.now()
        sixty_days_ago = today_dt - timedelta(days=60)
        sixty_days_ago_utc = sixty_days_ago.astimezone(timezone.utc)
        sixty_days_ago_iso = sixty_days_ago_utc.isoformat()
        
        # Delete from Supabase table
        supabase.supabase.table("audit_logs").delete().eq("user_id", session.uid).lt("created_at", sixty_days_ago_iso).execute()
        print(f"DEBUG: Cleaned up old audit logs older than {sixty_days_ago_iso}")
    except Exception as e:
        print(f"Error during auto-cleanup of old audit logs: {e}")

    try:
        rows = supabase.get_audit_logs(session.uid, limit=limit)
        logs: list[AuditLogResponse] = []
        
        now_utc = datetime.now(timezone.utc)
        user_local_time = now_utc + timedelta(minutes=tz_offset_min)
        
        # Calculate Monday and first_of_month in client local time
        user_monday = (user_local_time - timedelta(days=user_local_time.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        user_first_of_month = user_local_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Convert client local Monday/first_of_month back to UTC
        monday_utc = user_monday - timedelta(minutes=tz_offset_min)
        first_of_month_utc = user_first_of_month - timedelta(minutes=tz_offset_min)
        
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

            # Try to parse structured JSON details (if present) so the frontend
            # can show the task title / record id and a friendlier event name.
            details_raw = row.get("details", "") or ""
            details_obj = None
            task_id_val = None
            event_val = row.get("action", "")
            try:
                if details_raw and details_raw.strip().startswith("{"):
                    details_obj = json.loads(details_raw)
            except Exception:
                details_obj = None

            if details_obj:
                # Prefer the structured record_id when available
                rid = details_obj.get("record_id") or details_obj.get("recordId")
                if rid:
                    task_id_val = str(rid)
                # Prefer action_type from structured details when present
                action_type = details_obj.get("action_type") or details_obj.get("action")
                if action_type:
                    event_val = action_type

            logs.append(
                AuditLogResponse(
                    id=str(row.get("id") or ""),
                    task_id=str(task_id_val) if task_id_val else None,
                    event=event_val,
                    timestamp_iso=created_at,
                    user_uid=row.get("user_id", ""),
                    extra=details_raw,
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
        
        # Log the reset action AFTER clearing logs, so there is at least one log showing the reset!
        supabase.log_structured_audit(
            user_id=session.uid,
            action="system_reset",
            module="System",
            user_name=session.display_name or session.username,
            user_email=session.email or "",
            record_id="",
            previous_value="All historical data",
            new_value="Clean slate",
            notes="Reset analytics data and cleared historical audit logs"
        )
    except Exception as e:
        print(f"Error resetting analytics for {session.uid}: {e}")
        return

