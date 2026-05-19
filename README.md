# RemindMe

A personal AI-powered task reminder app.

**Stack:**
- 🎯 **Frontend**: Flutter (Chrome / Windows desktop)
- 🐍 **Backend**: Python 3.10 + FastAPI (fully offline, no cloud dependencies)
- 🔐 **Storage**: Encrypted local SQLite per user (AES via PyCryptodome)

---

## Project Structure

```
RemindMe/
├── mobile_flutter/        # Flutter frontend (Material 3, Provider)
│   ├── lib/
│   │   ├── main.dart
│   │   ├── app.dart
│   │   ├── core/          # AppState, ApiClient
│   │   ├── models/        # Task, Session, Analytics, AssistantReply
│   │   └── screens/       # Login, Home, Tasks, Dashboard, Assistant, Settings
│   └── pubspec.yaml
├── backend_api/           # FastAPI Python server
│   ├── app/
│   │   ├── main.py        # FastAPI entry point
│   │   ├── schemas.py     # Pydantic models
│   │   ├── routers/       # auth, tasks, assistant, analytics
│   │   └── services/      # task_service, session_store, analytics_service, assistant_service
│   ├── requirements.txt
│   └── .env               # Local dev config (not committed)
├── backend/               # Shared Python utilities
│   ├── crypto.py          # AES encrypt/decrypt + key derivation
│   ├── storage.py         # SQLite CRUD
│   ├── ai_assistant.py    # Offline NLP task parser (no API keys needed)
│   ├── stats_service.py
│   └── audit.py
├── run_backend.ps1        # ▶ Start the Python API
└── run_flutter.ps1        # ▶ Start the Flutter app
```

---

## Running Locally

### Prerequisites
- Python 3.10+
- Flutter 3.41.9 stable (at `C:\flutter_windows_3.41.9-stable\flutter`)

### 1. Start the Python Backend

```powershell
.\run_backend.ps1
```

API runs at **http://127.0.0.1:8000**  
Interactive docs: **http://127.0.0.1:8000/docs**

> First time only — the venv is auto-detected. If missing, run:
> ```powershell
> cd backend_api
> python -m venv .venv
> .\.venv\Scripts\pip install -r requirements.txt
> ```

### 2. Start the Flutter App

Open a **second terminal** and run:

```powershell
# Chrome (default)
.\run_flutter.ps1

# Windows desktop
.\run_flutter.ps1 -Target windows
```

App opens at **http://localhost:3000** (Chrome) or as a native window.

### 3. Log In

Use any credentials you like — the app creates an encrypted local database per user.

| Field | Default |
|-------|---------|
| Python API URL | `http://127.0.0.1:8000` |
| Username | *(your choice)* |
| Email | *(your choice)* |
| Local encryption secret | *(your choice — remember it!)* |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/auth/dev-login` | Start encrypted local session |
| GET | `/api/v1/tasks` | List tasks |
| POST | `/api/v1/tasks` | Create task |
| PUT | `/api/v1/tasks/{id}` | Update task |
| POST | `/api/v1/tasks/{id}/complete` | Mark complete |
| POST | `/api/v1/tasks/{id}/snooze` | Snooze task |
| DELETE | `/api/v1/tasks/{id}` | Delete task |
| POST | `/api/v1/assistant/message` | Chat with offline AI assistant |
| GET | `/api/v1/analytics/summary` | Dashboard analytics |

---

## Notes

- No external API keys required — the AI assistant is fully offline.
- All task data is AES-encrypted locally; nothing is sent to any cloud.
- The Flutter app uses hot-reload: press `r` in the Flutter terminal to reload after code changes.
