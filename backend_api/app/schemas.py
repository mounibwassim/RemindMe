from typing import Optional

from pydantic import BaseModel, Field


# ── Auth ──────────────────────────────────────────────────────────────────────

class DevLoginRequest(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    email: str = Field(min_length=3, max_length=255)
    secret: str = Field(min_length=4, max_length=255)


class RegisterRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=64)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=255)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=255)


class ForgotPasswordRequest(BaseModel):
    username: str = Field(min_length=1, max_length=255)


class ConfirmPasswordResetRequest(BaseModel):
    reset_code: str = Field(min_length=1, max_length=2048)
    new_password: str = Field(min_length=8, max_length=255)
    email: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=255)
    new_password: str = Field(min_length=8, max_length=255)


class SessionResponse(BaseModel):
    session_id: str
    username: str
    email: str


class AuthSessionResponse(BaseModel):
    session_id: str
    username: str
    display_name: str
    email: str
    uid: str
    avatar_emoji: Optional[str] = None


class AvatarUpdateRequest(BaseModel):
    avatar_emoji: str = Field(min_length=0, max_length=255)


# ── Tasks ─────────────────────────────────────────────────────────────────────

class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    due_iso: str
    priority: int = Field(default=3, ge=1, le=3)
    category: str = "General"
    sound: str = "Default"
    description: str = ""


class TaskUpdateRequest(TaskCreateRequest):
    pass


class TaskResponse(BaseModel):
    id: str
    title: str
    due_iso: str
    priority: int
    notified: int
    created_iso: str | None = None
    completed_iso: str | None = None
    category: str = ""
    sound: str = "Default"
    description: str = ""
    is_overdue: int = 0
    status: str = "open"
    notification_status: str = "pending"


class SnoozeTaskRequest(BaseModel):
    minutes: int = Field(default=10, ge=1, le=1440)


class NotificationEventRequest(BaseModel):
    event: str = Field(pattern="^(notification_scheduled|notification_triggered|opened|dismissed|notification_test|reminder_missed|snoozed_from_notification|completed_from_notification|missed)$")
    extra: str = ""
    notification_scheduled_at: Optional[str] = None


class MessageResponse(BaseModel):
    message: str


# ── Assistant ─────────────────────────────────────────────────────────────────

class AssistantRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    client_time: Optional[str] = None


class AssistantResponse(BaseModel):
    type: str
    response: str
    task: dict


# ── Analytics ─────────────────────────────────────────────────────────────────

class AnalyticsSummaryResponse(BaseModel):
    total_tasks: int
    completed: int
    pending: int
    upcoming: int
    weekly_labels: list[str]
    weekly_counts: list[int]
    weekly_range: str
    audit: dict
    completion_rate: float = 0.0
    ai_insight: str = ""
    completed_this_week: int = 0
    snoozed_this_week: int = 0
    created_this_week: int = 0


class AuditDetailResponse(BaseModel):
    notifications_sent: int
    notifications_opened: int
    snoozed_events: int
    completed_tasks: int
    created_tasks: int
    avg_response_min: float
    total_actions: int
    notification_open_rate: float


class PriorityBreakdownResponse(BaseModel):
    high: int
    medium: int
    low: int


class CalendarDayTask(BaseModel):
    id: str
    due: str
    completed: Optional[str] = None
    priority: int
    category: str


class CalendarMonthResponse(BaseModel):
    days: dict[str, list[CalendarDayTask]]


class AuditLogResponse(BaseModel):
    id: str
    task_id: str | None = None
    event: str
    timestamp_iso: str
    user_uid: str | None = ""
    extra: str | None = ""
    notification_scheduled_at: str | None = None
    notification_sent_at: str | None = None


# ── Custom OTP password recovery requests ───────────────────────────────────

class VerifyOtpRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    otp_code: str = Field(min_length=6, max_length=6)


class ResetPasswordRequest(BaseModel):
    reset_token: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=255)


class ChatMessageResponse(BaseModel):
    role: str
    content: str
    created_at: str

