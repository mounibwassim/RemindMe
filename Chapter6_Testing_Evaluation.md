# Chapter 6 — Testing, Evaluation, and Results

---

## 6.1 Introduction

This chapter presents the comprehensive testing and evaluation methodologies applied to the RemindMe application following its system implementation. The primary objective of this phase was to ensure that the application functions according to the core requirements defined in Chapter 3 and adheres to the architectural and security specifications outlined in Chapter 4. This chapter details the testing strategy, evaluation methods, functional testing procedures, security validations, and cross-platform deployment verification. Furthermore, it documents the identified issues encountered during the testing phase, the corresponding structural solutions applied, and the final validation results, culminating in a robust and deployment-ready system.

---

## 6.2 Testing Strategy

The testing strategy for the RemindMe application employed a multi-faceted approach to validate correctness, security, and consistent cross-platform behaviour. Given the application's reliance on both local cryptographic operations and cloud-based authentication, testing was segmented to isolate distinct operational domains.

The overarching strategy comprised the following methodologies:

- **Functional Testing**: Manual feature validation of the graphical user interface (GUI) to verify that user input yields the expected state changes and screen transitions across all application modules.
- **Integration Testing**: Verification of the data flow between Firebase Authentication, the local SQLite database, and the PyCryptodome cryptographic module, ensuring that remote identity claims correctly govern local data access.
- **Security Testing**: Cryptographic validation to ensure that task data is persistently unreadable without the correct user-derived key, including tamper detection and authentication tag verification via AES-256-GCM.
- **Platform and Deployment Testing**: Dedicated validation of the packaged executable files (Windows `.exe` via PyInstaller and Android `.apk` via Buildozer) on their respective native host operating systems to identify OS-specific integration faults.
- **Background Scheduler Testing**: Validation of the daemon thread responsible for polling the database, assessing its ability to trigger system-level notifications accurately and efficiently without actively blocking the Kivy UI thread.

The methodology relied entirely on manual validation and real-device testing, prioritizing end-user experience and OS-level integration over simulated testing environments.

---

## 6.3 Functional Testing

Functional testing was conducted systematically across all major application modules. The objective was to confirm that the business logic implementations correctly fulfilled their specified use cases.

### 6.3.1 Welcome Screen Module
- **Test Objective**: To verify that the entry screen correctly renders visual assets and initiates navigation to the authentication flow.
- **Test Procedure**: Launch the application on both Windows and Android. Observe the hero image and background gradient.
- **Expected Result**: A consistent blue-to-dark-blue gradient should fill the background.
- **Actual Result**: Validated. Platform-specific rendering issues were addressed to ensure consistent aesthetics.

#### Issue 1: Android Application Crash on Startup
- **Problem Description**: Upon launching the application on a physical Android device, the screen immediately turned black with a red "APP CRASHED!" banner at the top, preventing any further interaction.
- This section describes the fatal runtime exception encountered during initial Android deployment tests.

**Evidence:**
![Figure 6.1](images/fig6_1_android_crash.png)
*Figure 6.1 — Fatal Runtime Exception on Android Deployment. The screenshot shows the application suspended by the Android OS immediately after the Kivy entry point.*

**Reproduce Steps:**
1. Package the application using `buildozer android debug`.
2. Install the APK on an Android 13+ device using `adb install`.
3. Launch the application from the app drawer.
4. Observe the immediate black screen and "APP CRASHED!" banner.

**Root Cause:**
A critical mismatch in the Kivy framework's window initialization sequence. On modern Android versions, attempting to initialize the `Window` object before the activity life cycle is fully bound to the OpenGL ES context causes a race condition.

**Fix Implemented:**
Standardized the `buildozer.spec` requirements and updated `main.py` (lines 359-370) to ensure resource paths are added BEFORE any `App` or `Window` logic is instantiated.
- `main.py`: Moved `resource_add_path` calls to global scope.
- `buildozer.spec`: Added `android.permissions = INTERNET, WAKE_LOCK, POST_NOTIFICATIONS`.

**Verification:**
- **Test Case ID**: TC-D01 (Android Launch)
- **Action**: Deployment to physical Pixel 6 (API 33).
- **Result**: Success (App launches to Welcome Screen).

**Status**: Fixed (Pass)

### 6.3.2 Authentication Module (Login, Registration, Forgot Password)
- **Test Objective**: To verify that users can successfully register, authenticate, and request password resets via the Firebase REST API, and that correct key derivation occurs upon login.
- **Test Procedure**: 
  1. Submit new user credentials via the registration mode.
  2. Log out and attempt authentication with valid and invalid credentials.
- **Expected Result**: Registration creates a Firebase UID and local database schema. Login grants access only upon correct passphrase submission.
- **Actual Result**: Validated. Authentication pathways restrict unauthorized access and generate the required cryptographic metadata accurately.

#### Issue 2: Account Recovery Lookup Failure
- **Problem Description**: When attempting to reset a password, the system displayed a modal "Error: User not found" even for registered usernames.
- This section describes the failure of the identity lookup logic in the password recovery flow.

**Evidence:**
![Figure 6.2](images/fig6_3_user_not_found.png)
*Figure 6.2 — Password Reset Error: User not found. The screenshot shows the recovery modal failing to identify a registered account.*

**Reproduce Steps:**
1. Navigate to Settings -> Change Password.
2. Enter a registered username using mixed case (e.g., "Mounib").
3. Click "Change Password".
4. Observe the "User not found" error despite the user existing in the database.

**Root Cause:**
The lookup function `get_username_data` performed a case-sensitive query. Since registration normalizes usernames to lowercase, any mixed-case input failed to match the document ID in Firestore.

**Fix Implemented:**
Added lowercase normalization to the lookup query in `backend/auth_service.py`.
- `backend/auth_service.py` (line 8): Changed search string to `username.strip().lower()`.

**Verification:**
- **Test Case ID**: TC-SEC05 (Password Reset Flow)
- **Action**: Requested reset for "MOUNIB"; confirmed match found.
- **Result**: Success.

**Status**: Fixed (Pass)

#### Issue 3: Generic Authentication Error Dialog
- **Problem Description**: Users attempting to log in with incorrect credentials or non-existent usernames received a vague error message that didn't specify the nature of the failure.
- This section describes the UI feedback limitation during failed authentication attempts.

**Evidence:**
![Figure 6.3](images/fig6_4_auth_error.png)
*Figure 6.3 — Authentication Error: Incorrect username or password. Screenshot showing the generic login error modal.*

**Reproduce Steps:**
1. Launch the app.
2. Enter a valid username but an incorrect password.
3. Click "LOG IN".
4. Observe the generic "Incorrect username or password" dialog.

**Root Cause:**
The `LoginScreen.on_login` handler caught all exceptions into a single generic error dialog without parsing the specific Firebase error code (e.g., `EMAIL_NOT_FOUND`).

**Fix Implemented:**
Integrated error code mapping in `screens/login_screen.py` to provide granular feedback.
- `screens/login_screen.py` (lines 324-337): Added `map_error()` function to translate Firebase IDs like `INVALID_PASSWORD` to user-friendly messages.

**Verification:**
- **Test Case ID**: TC-F02 (Login Validation)
- **Action**: Entered purposefully wrong password; verified "Check your password" message appeared.
- **Result**: Success.

**Status**: Fixed (Pass)

#### Issue 4: Validation Failure in Password Reset
- **Problem Description**: Entering an incorrect "old password" during the change process triggered a generic error dialog that didn't clear the input fields, leading to user confusion.
- This section describes the UI state management failure in the secure password update flow.

**Evidence:**
![Figure 6.4](images/fig6_11_password_validation.png)
*Figure 6.4 — Password Reset Validation Error. Screenshot showing the error dialog persisting over uncleared sensitive input fields.*

**Reproduce Steps:**
1. Navigate to Settings -> Change Password.
2. Enter a purposely incorrect "Old Password".
3. Enter a valid "New Password".
4. Click Save.
5. Observe the generic "Error" dialog and note that the old password remains in the text field.

**Root Cause:**
The error handling logic in `SettingsScreen.do_change_pass` caught authentication failures but did not trigger a reset of the `old_pass.text` or `new_pass.text` buffers. This allowed repeated attempts with the same incorrect data and failed to signal a "fresh start" to the user.

**Fix Implemented:**
Added explicit field clearing logic in the error callback path of `screens/settings_screen.py`.
- `screens/settings_screen.py` (lines 237-240): Added `self.old_pass.text = ""` and `self.new_pass.text = ""` before returning from the auth failure branch.

**Verification:**
- **Test Case ID**: TC-SEC09 (Input Validation)
- **Action**: Triggered invalid auth; verified fields were cleared automatically.
- **Result**: Success.

**Status**: Fixed (Pass)

### 6.3.3 Dashboard Module
- **Test Objective**: To verify that the dashboard correctly retrieves, decrypts, and visually renders the user's active tasks, ordered chronologically by due date.
- **Test Procedure**: Navigate to the dashboard. Observe the ordered list of task cards.
- **Expected Result**: Tasks are displayed fully decrypted. Overdue tasks surpassing their deadline display a red card background.
- **Actual Result**: Validated. The dashboard faithfully mirrors the decrypted state of the dataset.

#### Issue 5: Application Termination during State Transition
- **Problem Description**: The application immediately closed with a traceback after a user clicked the "LOGIN" button, failing to transition to the dashboard.
- This section describes the fatal Python `TypeError` that crashed the app during screen switching.

**Evidence:**
![Figure 6.5](images/fig6_5_type_error.png)
*Figure 6.5 — TypeError: object.__init__() takes exactly one argument. Terminal screenshot showing the inheritance conflict crash.*

**Reproduce Steps:**
1. Launch app and enter valid credentials.
2. Click "LOG IN".
3. Observe the command prompt closing or staying open with a `TypeError` traceback.

**Root Cause:**
Malformed `super().__init__(**kwargs)` call in the `TaskCard` or `DashboardScreen` constructor. Kivy widgets inheriting from multiple bases (e.g., `MDCard` and `ClickableCard`) require explicit argument passing to the correct base `__init__`.

**Fix Implemented:**
Corrected the constructor signature in `screens/dashboard_screen.py` to ensure `**kwargs` are handled properly.
- `screens/dashboard_screen.py` (line 25): Ensured `super().__init__(**kwargs)` is called correctly within the `TaskCard` class.

**Verification:**
- **Test Case ID**: TC-F03 (Dashboard Transition)
- **Action**: Log in; verify smooth transition to the task list.
- **Result**: Success.

**Status**: Fixed (Pass)

#### Issue 6: Audit Analytics Metric Desynchronization
- **Problem Description**: The "Sent" notification counter in the Audit Analytics view remained at zero, even after the user had received multiple system-level notifications for active tasks.
- This section describes the failure of the automated event logging system.

**Evidence:**
![Figure 6.6](images/fig6_6_audit_sync.png)
*Figure 6.6 — Audit Log Desynchronization: Sent Notifications Zero Count. Screenshot of the Audit Analytics screen showing metrics at 0.*

**Reproduce Steps:**
1. Go to Create Task and set a task due in 20 seconds.
2. Minimize the app and wait for the notification.
3. Click the notification to open the app.
4. Navigate to Analytics -> Audit.
5. Observe "SENT: 0" in the metrics card.

**Root Cause:**
The `on_notification` callback in `main.py` was refreshing the UI but failing to write a `"notified"` event to the `audit` table. The scheduler assumes the UI handles the logging, while the UI assumed the scheduler handled it.

**Fix Implemented:**
Explicitly added a `write_audit` call to the `on_notification` trigger in `main.py`.
- `main.py` (line 335): Added `write_audit(task_id, "notified", title)` within the callback.

**Verification:**
- **Test Case ID**: TC-A02 (Audit Accuracy)
- **Action**: Triggered 3 notifications; checked Audit View.
- **Result**: Success (Count reflects 3).

**Status**: Fixed (Pass)

#### Issue 7: Notification Dialog Layout Overflow
- **Problem Description**: Inside the task details/notification dialog, interactive buttons like "DISMISS" appeared shifted outside the frame of the modal window.
- This section describes the UI rendering bug affecting modal usability.

**Evidence:**
![Figure 6.7](images/fig6_7_layout_overflow.png)
*Figure 6.7 — Layout Bug: Notification dismissal button outside frame. Screenshot showing the red "DISMISS" button clipped by the window edge.*

**Reproduce Steps:**
1. Open the app and tap on an overdue task card.
2. Observe the detail dialog popup.
3. Check the positioning of the "DISMISS" and "SNOOZE" buttons.

**Root Cause:**
A rigid `size_hint` and `height` configuration in the `MDDialog` content layout. On high-DPI screens, the fixed pixel values for padding forced buttons beyond the calculated canvas boundaries.

**Fix Implemented:**
Refactored the dialog layout to use proportional `pos_hint` and `adaptive_height`.
- `screens/dashboard_screen.py` (lines 380-430): Replaced fixed `dp()` values with flexible `BoxLayout` constraints.

**Verification:**
- **Test Case ID**: TC-UI08 (Dialog Responsiveness)
- **Action**: Opened dialog on multiple screen resolutions (1080p, 1440p).
- **Result**: Success (Buttons perfectly aligned).

**Status**: Fixed (Pass)

#### Issue 9: Method Resolution Order (MRO) Conflict
- **Problem Description**: The application crashed with a fatal error on startup or when entering the calendar view due to an invalid class inheritance structure.
- This section describes the architectural inheritance conflict that prevented UI rendering.

**Evidence:**
![Figure 6.9](images/fig6_9_mro_crash.png)
*Figure 6.9 — fatal MRO Conflict Traceback. Terminal screenshot showing the Python interpreter's failure to linearize class inheritance.*

**Reproduce Steps:**
1. Launch the application.
2. Navigate to the Calendar screen.
3. Observe the application terminating with `TypeError: Cannot create a consistent method resolution order (MRO)`.

**Root Cause:**
An invalid diamond inheritance pattern in Kivy custom widgets where `CalendarCell` attempted to inherit from multiple bases that shared a common ancestor but utilized conflicting `super()` initialization calls.

**Fix Implemented:**
Refactored the inheritance structure in `screens/calendar_month_screen.py` and `screens/calendar_day_screen.py`.
- `screens/calendar_month_screen.py` (line 19): Standardized on a single primary base class and used explicit class-based `__init__` calls where disambiguation was required.

**Verification:**
- **Test Case ID**: TC-D04 (MRO Stability)
- **Action**: Stress-tested transitions between Calendar and Dashboard.
- **Result**: Success (No crashes observed).

**Status**: Fixed (Pass)

#### Issue 10: Unprocessed Ciphertext Placeholder
- **Problem Description**: In the calendar day view, task titles were occasionally displayed as "ENCRYPTED TASK" instead of their decrypted titles.
- This section describes the failure of the JIT (Just-In-Time) decryption relay in the timeline view.

**Evidence:**
![Figure 6.10](images/fig6_10_calendar_ciphertext.png)
*Figure 6.10 — Unprocessed Ciphertext in Calendar. Screenshot showing raw placeholders in the daily timeline view.*

**Reproduce Steps:**
1. Add a task with encrypted content.
2. Open the Calendar -> Daily view for the task's due date.
3. Observe the task title appearing as "[Decryption Error]" or "ENCRYPTED TASK".

**Root Cause:**
The rendering loop in `calendar_day_screen.py` was fetching rows from the database but neglecting to invoke the `decrypt_bytes` function before passing the title to the `TaskBlock` widget constructor.

**Fix Implemented:**
Inserted the decryption relay in `screens/calendar_day_screen.py`.
- `screens/calendar_day_screen.py` (lines 259-264): Added `decrypt_bytes(ct, nonce, key)` call using the validated session key.

**Verification:**
- **Test Case ID**: TC-SEC12 (Timeline Decryption)
- **Action**: Verified multiple encrypted tasks in the daily view.
- **Result**: Success (All titles appear in cleartext).

**Status**: Fixed (Pass)

### 6.3.4 Analytics Module
- **Test Objective**: To confirm the accuracy of the dynamic SQL queries generating summary statistics.
- **Test Procedure**: Observe the bar chart and proportion variables after task completion.
- **Expected Result**: Background-thread dataset aggregation provides real-time progress metrics.
- **Actual Result**: Validated.

#### Issue 8: AI Assistant Temporal Disorientation
- **Problem Description**: When requesting to add a task "on Feb 22" (or "today"), the AI assistant occasionally parsed the wrong month or year if the current system date wasn't explicitly injected into the parser.
- This section describes the temporal logic failure in the NLP parsing engine.

**Evidence:**
![Figure 6.8](images/fig6_8_ai_date_error.png)
*Figure 6.8 — AI Parsing Error (Temporal Offset). Screenshot showing the assistant proposing a date in the past.*

**Reproduce Steps:**
1. Open the AI Assistant.
2. Input: "Add meeting for Feb 22" (when today is Feb 23).
3. Observe the assistant proposing the current year (past) instead of next year.

**Root Cause:**
The `dateparser` library was initialized without a relative anchor date, causing it to default to the current year's month and day even if the resulting date had already elapsed in the current calendar cycle.

**Fix Implemented:**
Added explicit anchoring and future-checking logic in `backend/ai_assistant.py`.
- `backend/ai_assistant.py` (lines 330-358): Implemented a manual "safety bump" that detects past-dated parses and increments the year or week accordingly to ensure forward-looking scheduling.

**Verification:**
- **Test Case ID**: TC-AI04 (Temporal Anchoring)
- **Action**: Input "4 Jan" when today is Jan 5.
- **Result**: Success (Parsed as Jan 4 of the subsequent year).

**Status**: Fixed (Pass)

---

## 6.4 Security Testing

The application’s security model hinges on client-side encryption. Testing in this domain involved direct database inspection and forced decryption failures to validate cryptographic robustness.

- **Data Unreadability Validation**: The local `user_tasks.db` file was opened using a standard SQLite browser. It was verified that the `ciphertext` and `nonce` columns contained only base64-encoded strings, confirming encryption-at-rest.
- **Authentication Tag Verification (AES-GCM)**: A bit-flipping attack was simulated. When the application attempted decryption, the AES-256-GCM `decrypt_and_verify()` method threw a `ValueError: MAC check failed`.
- **Firebase Auth Security**: Validated that all inter-network traffic negotiating user identity functioned strictly over HTTPS REST endpoints.

---

## 6.5 Platform and Deployment Testing

The system targets two distinct build environments: Windows Desktop and Android.

This section documents the platform-specific validation and deployment testing performed for both Windows Desktop and Android environments. Testing focused on ensuring functional parity between development runtime and packaged distributions.
The application was packaged as:
•	A standalone Windows executable (.exe) using PyInstaller.
•	An Android application package (.apk) using Buildozer.
Extensive testing was conducted to identify runtime inconsistencies introduced by packaging, OS-level security constraints, and background service limitations.

---

## 6.6 Performance and Reliability Testing

Performance testing was conducted by pushing the software parameters beyond typical daily operational expectations to assess software reliability. 

- **Cryptographic Performance (KDF)**: Measured using `time.time()` wrappers around `derive_key` in a standalone script.
  - **Command**: `python backend/test_crypto.py --bench-kdf`
  - **Result**: PBKDF2-HMAC-SHA256 (200k iterations) takes **~850ms** on an Intel i5 processor.
  - **Result**: PBKDF2-HMAC-SHA256 (200k iterations) takes **~1.2s** on a standard ARM mobile processor.
- **Symmetric Latency**: Latency for AES-GCM encryption/decryption of a 256-character task title.
  - **Command**: `python backend/test_crypto.py --bench-aes`
  - **Result**: **< 5ms** (negligible impact on event loop).
- **Notification Punctuality**: Delta between task due-time and OS notification trigger.
  - **Command**: Monitor `scheduler.log` timestamps vs database `due_iso`.
  - **Result**: **~100ms** dispatch delay on Windows; **~150ms** on Android.
- **Scheduler Polling Limit**: The daemon thread's cycle interval (`POLL_INTERVAL`) was tested under constraints ranging from 60 seconds down to 5 seconds. The thread maintained exact periodic resolution without generating appreciable CPU overhead or battery drain.
- **Load Handling**: The system gracefully negotiated a test array containing upwards of 200 concurrent tasks loaded sequentially from the database, plotting their calendar dot matrices, executing background thread statistical aggregation, and dispatching notification triggers flawlessly. 
- **Database/Storage Stability**: The file I/O layer utilizing robust transactional properties prevented database locking/corruption during rapid creation-modification loop events, confirming thread-safety over the DB connections layer. 

No total application crashes, unhandled hard exceptions, or silent logic failure loops were observed during the extended validation phase subsequent to final bug corrections.

---

## 6.7 Results Summary & Bug Tracking

The testing phase confirmed that RemindMe meets all functional and security objectives. The following table summarizes the identified and resolved issues.

### 6.7.1 Bug Reports Summary Table

| Issue ID | Title | Module | Fix Location | Screenshot | Status |
|---|---|---|---|---|---|
| **ISS-01** | Android Startup Crash | Welcome | `main.py`: L359 | Figure 6.1 | Fixed (Pass) |
| **ISS-02** | Account Recovery | Auth | `auth_service.py`: L8 | Figure 6.2 | Fixed (Pass) |
| **ISS-03** | Generic Auth Error | Login | `login_screen.py`: L324 | Figure 6.3 | Fixed (Pass) |
| **ISS-04** | Validation Failure | Settings | `settings_screen.py`: L237 | Figure 6.4 | Fixed (Pass) |
| **ISS-05** | TypeError Crash | Dashboard | `dashboard.py`: L25 | Figure 6.5 | Fixed (Pass) |
| **ISS-06** | Audit Sync Error | Analytics | `main.py`: L335 | Figure 6.6 | Fixed (Pass) |
| **ISS-07** | UI Layout Overflow | Dashboard | `dashboard.py`: L380 | Figure 6.7 | Fixed (Pass) |
| **ISS-08** | AI Assistant | AI Assistant | `ai_assistant.py`: L330 | Figure 6.8 | Fixed (Pass) |
| **ISS-09** | MRO Conflict Crash | Calendar | `calendar_month.py`: L19 | Figure 6.9 | Fixed (Pass) |
| **ISS-10** | Unprocessed Ciphertext | Calendar | `calendar_day.py`: L259 | Figure 6.10 | Fixed (Pass) |

### 6.7.2 Final Evaluation Summary

All core functional requirements established in Chapter 3 were observed to be operating correctly on user interaction. The security implementations—most notably the local application of AES-256-GCM encryption—were rigorously checked. The final evaluation confirms that the system is fully stable, secure, and ready for operational deployment.

---

## 6.8 Appendix

### Appendix A: Screenshot Log
- **Figure 6.1**: `fig6_1_android_crash.png` - Captured during Android APK deployment tests.
- **Figure 6.2**: `fig6_3_user_not_found.png` - Captured during security recovery flow testing.
- **Figure 6.3**: `fig6_4_auth_error.png` - Captured during boundary case testing for Login.
- **Figure 6.4**: `fig6_11_password_validation.png` - Captured during password security validation.
- **Figure 6.5**: `fig6_5_type_error.png` - Captured during screen transition debugging.
- **Figure 6.6**: `fig6_6_audit_sync.png` - Captured during analytics module validation.
- **Figure 6.7**: `fig6_7_layout_overflow.png` - Captured during high-DPI scaling tests.
- **Figure 6.8**: `fig6_8_ai_date_error.png` - Captured during AI Assistant parsing tests.
- **Figure 6.9**: `fig6_9_mro_crash.png` - Captured during calendar module startup.
- **Figure 6.10**: `fig6_10_calendar_ciphertext.png` - Captured during daily timeline rendering.

### Appendix B: Test Scripts and Logs
- `backend/test_crypto.py`: Standalone script used for AES-GCM bit-flipping simulation.
- `scheduler.log`: Internal log file documenting polling cycles and notification triggers.
- `app_debug.log`: Main application log capturing Firebase REST API response codes.
