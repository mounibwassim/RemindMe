# RemindMe Flutter + Python Migration

## Goal

Move only the mobile frontend from KivyMD to Flutter while preserving the Python
backend logic that gives the project its FYP identity: encryption, task
processing, scheduler rules, audit analytics, database operations, and offline
assistant parsing.

## Target Architecture

```text
Flutter mobile app
  - UI and navigation
  - Android/iOS builds
  - local notifications
  - charts and calendar
  - calls Python API over HTTP

Python FastAPI backend
  - encryption
  - task CRUD
  - SQLite database
  - audit analytics
  - AI assistant parser
  - reminder business rules
```

## Migration Phases

### Phase 1: Parallel Scaffold

Status: started.

- Keep Kivy project untouched.
- Add `backend_api/` as a FastAPI wrapper around existing Python modules.
- Add `mobile_flutter/` as the new Flutter frontend source.
- Use temporary `/api/v1/auth/dev-login` sessions for local integration.

### Phase 2: Feature Parity

- Port Kivy dashboard into Flutter.
- Port task creation/edit/edit/delete flows.
- Port assistant chat and confirmation workflow.
- Port analytics and audit screens.
- Port calendar day/month screens.
- Add Flutter local notifications.

### Phase 3: Production Auth

- Replace dev sessions with Firebase ID token verification.
- Move API secrets to environment variables.
- Store mobile tokens using `flutter_secure_storage`.
- Add refresh/logout handling.

### Phase 4: Deployment

- Generate Flutter Android/iOS project files.
- Configure launcher icon, splash screen, app signing, and app versioning.
- Deploy Python API using Docker.
- Build release APK/AAB from Flutter.

## Build Commands

Python API:

```bash
cd backend_api
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Flutter app:

```bash
cd mobile_flutter
flutter create .
flutter pub get
flutter run
flutter build apk --release
```

## API Contract

Current endpoints:

```text
GET    /health
POST   /api/v1/auth/dev-login
GET    /api/v1/tasks
POST   /api/v1/tasks
PUT    /api/v1/tasks/{task_id}
POST   /api/v1/tasks/{task_id}/complete
POST   /api/v1/tasks/{task_id}/snooze
DELETE /api/v1/tasks/{task_id}
POST   /api/v1/assistant/message
GET    /api/v1/analytics/summary
GET    /api/v1/analytics/audit
```

The Flutter app sends the temporary `X-Session-Id` header after login. In the
production phase, replace this with a Firebase bearer token.

## What Still Needs Building

- Native Flutter notification scheduling.
- Calendar screen parity.
- Full audit analytics screen parity.
- Firebase production auth.
- API tests.
- Flutter widget tests.
- Android signing configuration.
