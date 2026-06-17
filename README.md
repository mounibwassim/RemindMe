# RemindMe 📋🤖

[![Flutter](https://img.shields.io/badge/Flutter-3.41.9%20stable-02569B?logo=flutter&logoColor=white)](https://flutter.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-v0.110.0-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Supabase](https://img.shields.io/badge/Supabase-Database%20%26%20RLS-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Platform](https://img.shields.io/badge/Platform-Android%20%7C%20iOS%20%7C%20Windows%20%7C%20Web-blue)](#)

A production-grade, highly resilient **Task Reminder Application** featuring a cross-platform **Flutter** client and high-performance **FastAPI** backend with cloud database synchronization, user isolation, and robust offline-first capabilities.

---

## 🌟 Key Features

### 1. 🤖 Natural Language Processing (NLP) Task Assistant
* **Natural Language Parsing**: Schedule reminders naturally. E.g., *"gym tomorrow at 8 am with high priority"* or *"study next Monday at 10 am"*.
* **Local NLP Engine**: Fast, offline-first regex-based parser extracts titles, dates, times, priorities, and categories instantly without calling external APIs.
* **Smart Auto-Categorization**: Automatically categorizes tasks based on text keywords into **11 categories**: *Gym, Study, Work, Health, Finance, Call, Family, Social, Home, Gaming, or Birthday*.
* **Safety Checks**: Rejects past-dated task creation and guides the user to schedule future-aware tasks.
* **Productivity Insights**: Algorithmic rules engine generates weekly and monthly motivational insights based on task completion trends and category bottlenecks.

### 2. ⚡ Resilient Offline-First Architecture
* **Offline Mutation Queue**: Perform edits, creations, completions, snoozing, and deletions completely offline. Mutations are queued locally via `SharedPreferences` and automatically replayed to the cloud database when internet access is restored.
* **Active Environment Self-Healing**: Automatically probes and determines the correct API URL (Android Emulator local host, web local server, or production Render server). Clears defunct cached/invalid custom URLs.
* **Warm-up Sequencer**: Handles Render Free Tier cold starts by providing a visual progress indicator and background retrying loops until the backend is fully awake.

### 3. 🔒 Robust Security & User Isolation
* **Supabase Security Policies (RLS)**: Enforces Row-Level Security on Supabase tables so users can only access their own tasks, audit logs, analytics, and chat messages.
* **Local Session Encryption (Optional)**: Support for encrypted local sessions using AES-256-GCM encryption and PBKDF2-HMAC-SHA256 key derivation.
* **OTP Password Reset Fallback**: Features an OTP-based password recovery engine tied to SMTP or Resend/Brevo fallback, replacing traditional links with secure code entry inputs.

### 4. 📊 Analytics & Audit Logging
* **Interactive Dashboard**: View task statistics, upcoming vs. overdue metrics, and visual week-by-week completion charts.
* **Real-time Sync**: A centralized state synchronization (`syncAll()`) pushes task changes immediately to dashboard widgets, analytics counters, and audit logs.
* **Automated Audit Logging**: Every mutation (create, edit, complete, delete, snooze) is fully logged to Supabase to build an unalterable history trail.
* **Missed Task Detection**: Scans for pending tasks whose due times have passed and transitions them to a "missed" status automatically.

### 5. 🎨 Customization & Premium UX
* **Emoji-based Avatar Picker**: Replace plain text placeholders with modern emoji/character avatars (Boy, Business, Cyberpunk, Gaming, Robot, etc.).
* **Material 3 Design**: Fully responsive screens, including Login, Home, Tasks, Calendar, Dashboard, History, Audit Logs, AI Assistant, and Settings.
* **Custom Calendar Picker**: Interactive custom calendar/time pickers customized for mobile screen framing (supports AM/PM and year-month selector).
* **Multi-Theme Support**: Instant switching between Light Mode, Dark Mode, and System Default.
* **System Notification Integration**: Seamless redirection to Android's system notification channel settings if permissions are denied, along with test alarm triggers.

---

## 📂 Project Structure

```text
RemindMe/
├── mobile_flutter/          # Flutter Frontend (Material 3, Provider)
│   ├── lib/
│   │   ├── main.dart        # Flutter entry point
│   │   ├── app.dart         # Main App routing & theme config
│   │   ├── core/            # AppState, ApiClient, NotificationService, WebNotifier
│   │   ├── models/          # Task, AnalyticsSummary, AuditLog, Session, AssistantReply
│   │   └── screens/         # Login, Home, Tasks, Dashboard, Calendar, History, Settings, Assistant, Audit, Warmup
│   ├── assets/              # Logos, custom avatar assets
│   ├── pubspec.yaml         # Dependencies (shared_preferences, http, provider, etc.)
│   └── web/                 # Web assets and manifest configurations
│
├── backend_api/             # FastAPI Python Server
│   ├── app/
│   │   ├── main.py          # FastAPI application init and CORS middleware
│   │   ├── schemas.py       # Pydantic schemas (TaskDraft, Auth, Analytics)
│   │   ├── deps.py          # Dependency injection helpers
│   │   ├── routers/         # Auth, Tasks, Assistant, Analytics, System endpoints
│   │   └── services/        # TaskService, SessionStore, AnalyticsService, AssistantService, InsightsService
│   ├── Dockerfile           # Docker image definition for production hosting
│   ├── requirements.txt     # Python requirements (fastapi, supabase, pydantic, pycryptodome)
│   └── .env                 # Environment secrets (Supabase API credentials, SMTP config)
│
├── backend/                 # Shared Core Python Library
│   ├── supabase_service.py  # Supabase client execution (CRUD for tasks, logs, analytics)
│   ├── supabase_auth.py     # Auth integrations and password reset fallback
│   ├── ai_assistant.py      # Local NLP parser logic
│   ├── email_service.py     # SMTP / Brevo / Resend client for OTP dispatch
│   ├── otp_store.py         # Local SQLite / In-memory storage for auth verification codes
│   ├── crypto.py            # Local AES encryption utilities
│   └── stats_service.py     # Stats/analytics calculation
│
├── run_backend.ps1          # ▶ script to activate venv and spin up FastAPI server
├── run_flutter.ps1          # ▶ script to spin up the Flutter UI client
├── reset_db.ps1             # ▶ utility to purge and format local databases
└── render.yaml              # Blueprint file to instantly spin up deployment on Render
```

---

## 🛠️ Running Locally

### Prerequisites
* **Flutter SDK**: 3.41.9 stable or newer
* **Python**: 3.10 or newer
* **Git** installed on your system

### 1. Backend Environment Setup
Navigate to the `backend_api` directory and create an `.env` file containing the credentials for your database and email delivery providers:

```ini
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_KEY=your-supabase-service-role-key
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
```

### 2. Launching the Backend Server
Run the PowerShell helper script in the root directory:

```powershell
.\run_backend.ps1
```

This will automatically create a Python virtual environment (`.venv`), install all requirements, and spin up the FastAPI service on:
* **API Address**: `http://127.0.0.1:8000`
* **Swagger Documentation**: `http://127.0.0.1:8000/docs`

### 3. Launching the Flutter Client
Open a new terminal session and run the Flutter launch script:

```powershell
# To run on Web (Chrome - Default)
.\run_flutter.ps1

# To run on Windows native desktop
.\run_flutter.ps1 -Target windows
```

The Flutter app will open in your browser or as a native Windows desktop client.

---

## 🐳 Production Deployment

### Docker Deployment
The backend includes a fully optimized `Dockerfile` in `backend_api/` for containerized environments. To build and run the API server container locally:

```bash
# Build the Docker image from root workspace
docker build -f backend_api/Dockerfile -t remindme-backend .

# Run the container
docker run -p 8000:8000 --env-file backend_api/.env remindme-backend
```

### Render Deployment
This repository is configured for instant hosting on Render using the `render.yaml` blueprint. Adding this repository to Render will automatically spin up:
1. A **Web Service** container built from `backend_api/Dockerfile`.
2. Necessary configuration mappings to link environment variables.

---

## 🧪 API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **GET** | `/health` | Server status checks and network testing |
| **POST** | `/api/v1/auth/register` | Create a new user account |
| **POST** | `/api/v1/auth/login` | Authenticate user and initiate session |
| **POST** | `/api/v1/auth/dev-login` | Start local encrypted SQLite developer session |
| **POST** | `/api/v1/auth/forgot-password` | Request password reset verification code (OTP) |
| **POST** | `/api/v1/auth/confirm-password` | Submit password reset OTP verification code |
| **GET** | `/api/v1/tasks` | Retrieve user-isolated tasks list |
| **POST** | `/api/v1/tasks` | Create new task item |
| **PUT** | `/api/v1/tasks/{id}` | Modify task item parameters |
| **DELETE** | `/api/v1/tasks/{id}` | Purge task item |
| **POST** | `/api/v1/tasks/{id}/complete` | Mark task as completed |
| **POST** | `/api/v1/tasks/{id}/snooze` | Postpone task due time by a minute count |
| **POST** | `/api/v1/assistant/message` | Send message to local NLP task assistant |
| **GET** | `/api/v1/analytics/summary` | Retrieve dashboard stats & completion trend |

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
