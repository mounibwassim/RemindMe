# RemindMe Python API

This folder is the new Python backend layer for the Flutter migration.

The existing Kivy project remains untouched. This API reuses the current Python
modules in `backend/` for encryption, SQLite storage, audit logging, analytics,
and the offline assistant parser.

## Run locally

```bash
cd backend_api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check:

```text
GET http://127.0.0.1:8000/health
```

## Mobile connection

Android emulators should call:

```text
http://10.0.2.2:8000
```

Physical phones should call your computer's LAN IP, for example:

```text
http://192.168.1.23:8000
```

## Current migration stage

This is an FYP-friendly API scaffold, not the final production security layer.
It already separates Flutter UI from Python business logic. The next step is to
replace the temporary dev session endpoint with Firebase ID-token verification.
