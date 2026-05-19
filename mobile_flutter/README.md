# RemindMe Flutter Client

This folder contains the Flutter source for the new mobile frontend.

Flutter is not installed on this machine yet, so native Android/iOS project
folders were not generated. After installing Flutter, run:

```bash
cd mobile_flutter
flutter create .
flutter pub get
flutter run
```

The existing `lib/` and `pubspec.yaml` files in this folder are the migration
starting point. If `flutter create .` asks about overwriting files, keep the
existing `lib/` and `pubspec.yaml` content.

## Backend URL

Run the Python API first:

```bash
cd ..\backend_api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Use this API base URL in the app:

- Android emulator: `http://10.0.2.2:8000`
- Physical phone: `http://YOUR_COMPUTER_LAN_IP:8000`
- Desktop/web debug: `http://127.0.0.1:8000`
