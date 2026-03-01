# Chapter 5 — System Implementation

---

## 5.1 Welcome Screen

paste it here , and write this figure: **Figure 5.1** — Welcome Screen

This section describes the Welcome Screen, which serves as the application's entry point upon initial launch. It is the first interface the user encounters and is designed to communicate the application's purpose and direct the user to the authentication interface. The screen is implemented entirely in `screens/welcome_screen.py` within the `WelcomeScreen` class, which extends `MDScreen` from the KivyMD framework. No separate KV layout file is used; all UI elements are constructed programmatically within the `build_ui()` method.

paste it here , and write this figure: Screenshot `screens/welcome_screen.py`, lines 20–50 — shows `build_ui()` initialisation and canvas gradient setup.

### UI Structure

The screen renders a full-viewport gradient background achieved via Kivy's `Canvas` API using a custom `Texture` object transitioning vertically from Sky Blue (`#87CEEB`) to Dodger Blue (`#1E90FF`). Two translucent `Ellipse` decorative orbs are layered on the canvas to create visual depth.

paste it here , and write this figure: Screenshot lines 146–153 — shows `_create_gradient()` texture buffer construction.

Centred over the background is a glassmorphic `MDCard` occupying 90% of the screen area with rounded corners (`radius=40`), a transparent fill (`md_bg_color=(1, 1, 1, 0.08)`), and a visible white border. The card contains a strict vertical hierarchy:

1. **Title Label** — "RemindMe" in `H3` bold, white, horizontally centred.
2. **Subtitle Label** — "Secure & Smart Task Management" in `Subtitle1`, light grey.
3. **Hero Image** — `assets/hero_robot.png` occupying 70% of the card height.
1.  **Title Label** — "RemindMe" in `H3` bold, white, horizontally centred.
2.  **Subtitle Label** — "Secure & Smart Task Management" in `Subtitle1`, light grey.
3.  **Hero Image** — `assets/hero_robot.png` occupying 70% of the card height.
4.  **GET STARTED Button** — A rounded `ClickableCard` (pill-shaped, `radius=28`) in cyan accent, labelled "GET STARTED" in `H6` bold white. Bound to `on_release=self.go_to_login`.

paste it here , and write this figure: Screenshot lines 109–128 — shows the GET STARTED `ClickableCard` with `on_release=self.go_to_login`.

### Implementation Logic

The `go_to_login()` method (line 155–157) is invoked when the user taps the GET STARTED button. It calls `App.get_running_app().switch_screen('login')`, which delegates to the `switch_screen()` method in `ReminderApp` (`main.py`). The `ScreenManager` then transitions to the `LoginScreen` using `NoTransition`.

paste it here , and write this figure: Screenshot lines 155–157 — shows `go_to_login()` delegating to `switch_screen('login')`.
No database interaction, network calls, or user state management occurs on this screen.

---

### Code Evidence

| Element | File | Function / Location | Lines |
|---|---|---|---|
| UI construction | `screens/welcome_screen.py` | `WelcomeScreen.build_ui()` | 20–137 |
| Background gradient | `screens/welcome_screen.py` | `WelcomeScreen._create_gradient()` | 146–153 |
| GET STARTED button | `screens/welcome_screen.py` | `ClickableCard`, `on_release=self.go_to_login` | 109–128 |
| Navigation handler | `screens/welcome_screen.py` | `WelcomeScreen.go_to_login()` | 155–157 |
| Screen registration | `main.py` | `ReminderApp.build()` | 159 |
| Navigation dispatcher | `main.py` | `ReminderApp.switch_screen()` | 181–190 |

---

---

**Testing Note:** For technical details regarding the resolution of Android gradient rendering failures, see **Issue 1 (Android Startup Crash)** in Chapter 6.

---

---

---

---

## 5.2 Login Screen

paste it here , and write this figure: **Figure 5.2** — Login Screen

This section describes the Login Screen, which provides the primary authentication interface for registered users of the RemindMe application. The screen is implemented in `screens/login_screen.py` within the `LoginScreen` class extending `MDScreen`. It integrates with `backend/firebase_service.py` for cloud authentication, `backend/auth_service.py` for username-to-credential resolution, `backend/storage.py` for local encrypted database management, and `backend/crypto.py` for key derivation.

### UI Structure

The Login Screen is fully constructed programmatically within the `on_enter()` method (lines 22–140), ensuring a clean state on each visit. Two primary visual sections are rendered:

1. **Header Card** — A rounded-bottom `MDCard` occupying the upper 35% of the viewport rendered in solid blue (`#3399FF`), containing the title "RemindMe" in bold `H3` white and the subtitle "Sign in to continue" in `Subtitle1` light grey.
2. **Content Card** — A centred `MDCard` at 50% vertical position containing:
   - **Username Field** (`MDTextField`, `mode="rectangle"`) — Pre-populated by `get_last_user(app.storage_path)` with the previously authenticated username.
   - **Password Field** (`MDTextField`, `password=True`) — Masked by default with a toggleable eye icon.
   - **LOG IN Button** (`MDRaisedButton`) — Bound to `on_release=self.on_login`.
   - **Create New Account** link — `MDFlatButton` triggering `toggle_mode()`.
   - **Forgot Password** link — `MDFlatButton` navigating to `ForgotPasswordScreen`.

paste it here , and write this figure: Screenshot `screens/login_screen.py`, lines 22–140 — shows the UI construction in `on_enter()`.

### Implementation Logic

The `on_login()` method (lines 204–322) executes the following authentication pipeline:

1. The username is normalised to lowercase and submitted to `get_username_data()` in `firebase_service.py`, which performs a POST request to the Firebase Firestore `runQuery` REST API endpoint to retrieve the account's email, encryption metadata (salt and wrapped DEK), and Firebase UID.

paste it here , and write this figure: Screenshot `screens/login_screen.py`, lines 204–230 — shows `on_login()` retrieving username data from cloud.
paste it here , and write this figure: Screenshot `backend/firebase_service.py`, lines 147–175 — shows the Firestore structured query block.

2. If the Firestore lookup succeeds, `sign_in_with_email_password()` (lines 39–62, `firebase_service.py`) authenticates against Firebase Authentication using the retrieved email and the entered passphrase.
3. On successful Firebase authentication, `ensure_account()` (lines 39–101, `storage.py`) decodes the base64 salt from cloud metadata, derives a user key via `derive_key()` in `crypto.py`, and unwraps the encrypted Data Encryption Key (DEK) using `decrypt_bytes()`. This step simultaneously verifies the passphrase's correctness — an incorrect passphrase yields a GCM authentication tag mismatch, raising a `ValueError`.

paste it here , and write this figure: Screenshot `backend/storage.py`, lines 80–101 — shows DEK unwrapping and the `ValueError` raised on key mismatch.
paste it here , and write this figure: Screenshot `backend/crypto.py`, lines 27–51 — shows `derive_key()` PBKDF2 and `decrypt_bytes()` AES-GCM.

4. On success, the application state is updated (`app.derived_key`, `app.db_path`, `app.current_user`, `app.current_uid`), the background scheduler is started via `start_scheduler()`, and the `ScreenManager` transitions to the Dashboard.

---

### Code Evidence

| Element | File | Function / Location | Lines |
|---|---|---|---|
| UI construction | `screens/login_screen.py` | `LoginScreen.on_enter()` | 22–140 |
| Login handler | `screens/login_screen.py` | `LoginScreen.on_login()` | 204–322 |
| Error dialog | `screens/login_screen.py` | `LoginScreen.show_error()` | 339–346 |
| Cloud user lookup | `backend/firebase_service.py` | `get_username_data()` | 147–220 |
| Firebase sign-in | `backend/firebase_service.py` | `sign_in_with_email_password()` | 39–62 |
| Local key derivation | `backend/storage.py` | `ensure_account()` | 39–101 |
| PBKDF2 key derive | `backend/crypto.py` | `derive_key()` | 27–29 |
| DEK decryption | `backend/crypto.py` | `decrypt_bytes()` | 42–51 |
| Scheduler start | `main.py` | `ReminderApp.start_scheduler()` | ~215–240 |

---

---

**Testing Note:** For technical details regarding the resolution of Firebase authentication and account lookup failures, see **Issue 4 (Incorrect Credentials)** in Chapter 6.

---

---

---

---

## 5.3 Create Account Screen

paste it here , and write this figure: **Figure 5.3** — Create Account Screen

This section describes the Create Account (Registration) interface. Rather than occupying a separate screen, registration is implemented as a modal state of the `LoginScreen` class in `screens/login_screen.py`, controlled by the `mode` attribute toggled via `toggle_mode()` (lines 173–202). Supporting modules include `backend/firebase_service.py`, `backend/auth_service.py`, `backend/storage.py`, and `backend/crypto.py`.

paste it here , and write this figure: Screenshot `screens/login_screen.py`, lines 173–202 — shows `toggle_mode()` revealing the email field.

### UI Structure

Activating registration mode via the "Create New Account" link reveals an additional `MDTextField` email field (hidden during login mode via `opacity=0` and `height=0`) and relabels the primary action button from "LOG IN" to "REGISTER". The Forgot Password link is hidden in this mode to reduce interface complexity. No layout rebuild is performed; widget visibility is toggled dynamically via property assignment.

### Implementation Logic

When "REGISTER" is pressed, the registration branch of `on_login()` (lines 225–270) executes:

1. `get_username_data()` is called to verify that the chosen username is not already registered in Firestore.
2. `sign_up_with_email_password()` (lines 64–86, `firebase_service.py`) submits the email and password to the Firebase Authentication REST API `accounts:signUp` endpoint, receiving a UID and ID token.
3. `ensure_account()` is called with `create_if_missing=True`. Internally, `gen_salt()` generates a 16-byte cryptographic random salt via `get_random_bytes(16)`. A 256-bit DEK is generated via `os.urandom(32)`. A user key is derived from `"{username}:{email}"` and the salt using PBKDF2-HMAC-SHA256 with 200,000 iterations. The DEK is then AES-256-GCM encrypted using this user key, and the encrypted DEK plus salt are returned as `new_metadata`.
4. The username, email, UID, and metadata are pushed to Firestore via `save_username_mapping()`.
5. The user's Firebase display name is set via `update_profile()`. An audit event `"REGISTER"` is written to the local database.

paste it here , and write this figure: Screenshot `screens/login_screen.py`, lines 225–270 — shows the registration branch: Firebase signup, `ensure_account()`, and `save_username_mapping()`.
paste it here , and write this figure: Screenshot `backend/crypto.py`, lines 11–40 — shows `gen_salt()`, `derive_key()`, and `encrypt_bytes()` forming the cryptographic registration pipeline.
paste it here , and write this figure: Screenshot `backend/storage.py`, lines 54–72 — shows `ensure_account()` create-mode: DEK generation and metadata assembly.

### Security Considerations

The plaintext passphrase is never stored at any stage. The KDF salt is generated using a cryptographically secure random number generator, guaranteeing per-user uniqueness. The stored metadata in Firestore contains only the salt and the encrypted DEK — no raw key or password derivative is exposed.

---

### Code Evidence

| Element | File | Function / Location | Lines |
|---|---|---|---|
| Registration logic | `screens/login_screen.py` | `LoginScreen.on_login()` (register branch) | 225–270 |
| Mode toggle | `screens/login_screen.py` | `LoginScreen.toggle_mode()` | 173–202 |
| Firebase sign-up | `backend/firebase_service.py` | `sign_up_with_email_password()` | 64–86 |
| Salt generation | `backend/crypto.py` | `gen_salt()` | 11–12 |
| Key derivation | `backend/crypto.py` | `derive_key()` | 27–29 |
| DEK encryption | `backend/crypto.py` | `encrypt_bytes()` | 31–40 |
| Account & DB init | `backend/storage.py` | `ensure_account()` (create branch) | 54–72 |
| Database tables | `backend/storage.py` | `init_db_for()` | ~140–200 |
| Audit on register | `backend/audit.py` | `write_audit()` | — |

---

---

**Testing Note:** For technical details regarding the resolution of registration-to-login data synchronization issues, see **Issue 2 (Firebase Initialization)** in Chapter 6.

---

---

---

---

## 5.4 Forgot Password Screen

paste it here , and write this figure: **Figure 5.4** — Forgot Password Screen

This section describes the Forgot Password Screen, which allows users to request a password reset link via email when they are unable to authenticate. The screen is implemented in `screens/forgot_password_screen.py`. Backend interaction is handled by `backend/firebase_service.py` via the `reset_password_email()` function.

### UI Structure

The screen follows the application's standard two-section layout: a blue rounded header card with a back-navigation arrow and a "Forgot Password" title, and a centred content card containing:
- An `MDTextField` accepting the user's registered email address.
- A "Send Reset Link" `MDRaisedButton`.
- A confirmation `MDLabel` dynamically shown on successful submission.
- A "Back to Login" `MDFlatButton`.

### Implementation Logic

When "Send Reset Link" is pressed, the handler validates that the email field is non-empty, then calls `reset_password_email(email)` in `firebase_service.py`. This function submits a POST request to the Firebase Authentication REST endpoint `accounts:sendOobCode` with `requestType: "PASSWORD_RESET"` and the user's email. The `X-Firebase-Locale: en` header ensures the reset email is delivered in English. Firebase generates a time-limited, single-use reset token, hashes it for secure server-side storage, and dispatches the reset link via email. Upon a successful API response, the confirmation label is made visible. On failure, the error code is parsed and an appropriate message is displayed.

paste it here , and write this figure: Screenshot `backend/firebase_service.py`, lines 13–37 — shows the full `reset_password_email()` function, including the locale header and error handling.
paste it here , and write this figure: Screenshot `screens/login_screen.py`, lines 324–337 — shows `map_error()` translating Firebase error codes to user-facing messages.

### Security Considerations

All token generation, hashing, expiration enforcement, and delivery are managed by Firebase Authentication. The client application does not generate or handle reset tokens. Token expiration defaults to one hour; the token is invalidated after use.

---

### Code Evidence

| Element | File | Function / Location | Lines |
|---|---|---|---|
| Reset email call | `backend/firebase_service.py` | `reset_password_email()` | 13–37 |
| Firebase API call | `backend/firebase_service.py` | `requests.post(url, json=payload)` | 30 |
| Error code mapping | `screens/login_screen.py` | `LoginScreen.map_error()` | 324–337 |

---

---

**Testing Note:** For technical details regarding the resolution of SMTP deliverability and locale headers, see **Issue 3 (Account Recovery/User Not Found)** in Chapter 6.

---

---

---

---

## 5.5 Dashboard Screen

paste it here , and write this figure: **Figure 5.5** — Dashboard Screen

This section describes the Dashboard Screen, which constitutes the primary operational interface following successful authentication. It is implemented in `screens/dashboard_screen.py` via the `DashboardScreen` class extending `MDScreen`. Task data is retrieved from `backend/storage.py` (`list_tasks`, `complete_task`, `delete_task`, `snooze_task`, `dismiss_notification`), decrypted via `backend/crypto.py` (`decrypt_bytes`), and audited via `backend/audit.py` (`write_audit`).

### UI Structure

The screen uses `MDBottomNavigation` with three tabs:

1. **Tasks Tab** — A fixed blue header card displays the current date (formatted as `"%a %d %b"`) and a right-aligned icon bar: create task (`plus-circle`), AI (`robot`), analytics (`chart-bar`), settings (`cog`), logout (`logout`). Below, a `ScrollView`-wrapped `MDList` renders active tasks as `TaskCard` widgets.
2. **Calendar Tab** — Navigates to `CalendarMonthScreen` on selection.
3. **History Tab** — Displays completed tasks in an `MDList`; a trash icon in the header offers bulk deletion via confirmation dialog.

Each `TaskCard` (custom `ClickableCard` subclass, lines 22–192) is a horizontal card with: a left priority colour bar (red=High, yellow=Medium, green=Low), priority and category icon pair, title and formatted due-date labels, and a right-side action cluster with complete (`check-circle-outline`) and delete (`delete-outline`) icon buttons. Overdue tasks receive a red background override.

### Implementation Logic

On `on_enter()` (lines 207–212), the UI is fully rebuilt via `build_ui()` to prevent rendering artefacts from stale widget state, then `refresh_tasks()` is called immediately. Within `refresh_tasks()` (lines 332–366), `list_tasks(self.app.db_path)` retrieves all rows from the SQLite `tasks` table ordered by `due_iso`. 

paste it here , and write this figure: Screenshot `backend/storage.py`, lines 341–350 — shows the `list_tasks()` SQL SELECT query returning 12 columns.

Each row's `ciphertext` and `nonce` are passed to `decrypt_bytes(ct, nonce, self.app.derived_key)` to recover the plaintext title. 

paste it here , and write this figure: Screenshot `screens/dashboard_screen.py`, lines 332–366 — shows `refresh_tasks()` calling `list_tasks()` and `decrypt_bytes()`.
paste it here , and write this figure: Screenshot `backend/crypto.py`, lines 42–51 — shows `decrypt_bytes()` AES-GCM decryption with tag verification.

Only tasks where `completed_iso` is `None` or empty are rendered. Tasks are sorted ascending by due date before display.

Tapping a task card invokes `show_task_options()` (lines 368–433), opening an `MDDialog` with: title, description, priority badge, due date, and conditional action buttons — snooze/dismiss for overdue tasks, edit/delete for pending tasks. Editing stores task data in `self.app.modify_task_data` and navigates to `CreateTaskScreen`.

---

### Code Evidence

| Element | File | Function / Location | Lines |
|---|---|---|---|
| Screen entry | `screens/dashboard_screen.py` | `DashboardScreen.on_enter()` | 207–212 |
| UI construction | `screens/dashboard_screen.py` | `DashboardScreen.build_ui()` | 220–330 |
| Task fetch + decrypt | `screens/dashboard_screen.py` | `DashboardScreen.refresh_tasks()` | 332–366 |
| Task detail dialog | `screens/dashboard_screen.py` | `DashboardScreen.show_task_options()` | 368–433 |
| Task card widget | `screens/dashboard_screen.py` | `TaskCard.__init__()` | 22–146 |
| Decrypt function | `backend/crypto.py` | `decrypt_bytes()` | 42–51 |
| SQLite query | `backend/storage.py` | `list_tasks()` | 341–350 |
| Complete task | `backend/storage.py` | `complete_task()` | 369–377 |
| Delete task | `backend/storage.py` | `delete_task()` | 379–388 |
| Snooze task | `backend/storage.py` | `snooze_task()` | 402–410 |
| Dismiss task | `backend/storage.py` | `dismiss_notification()` | 360–367 |

---

---

**Testing Note:** For technical details regarding the resolution of notification scheduler failures and row unpacking errors, see **Issue 6 (Audit Sync)** in Chapter 6.

---

---

---

---

## 5.6 Create Task Screen

paste it here , and write this figure: **Figure 5.6** — Create Task Screen

This section describes the Create Task Screen, which provides the form interface for both creating new tasks and editing existing ones. It is implemented in `screens/create_task_screen.py` via the `CreateTaskScreen` class extending `MDScreen`. It interacts with `backend/storage.py` (`save_task`, `update_task`), `backend/crypto.py` (`encrypt_bytes`), and `backend/audit.py` (`write_audit`).

### UI Structure

The interface is constructed in `load_view()` (lines 56–268), called on each `on_enter()` event. A vertical `MDBoxLayout` root container holds:

1. **Header Card** — Blue rounded header with a back arrow and the screen title ("Create New Task" or "Modify Task" depending on mode).
2. **Scrollable Content** — An `MDScrollView` wrapping a dynamically sized `MDBoxLayout` containing:
   - **Title Field** (`MDTextField`) — Required single-line text input.
   - **Description Field** (`MDTextField`, `multiline=True`) — Optional 100dp-height text area.
   - **Date + Time Row** — Two `MDRoundFlatIconButton` controls launching `MDDatePicker` and `MDTimePicker` modal dialogs.
   - **Priority Row** — Three `MDRaisedButton` controls for Low, Medium, High. Active selection highlighted in green/yellow/red via `set_priority()` (lines 302–320).
   - **Category Grid** — A 3×3 `MDGridLayout` of `CategoryChip` icon-button cells (Work, Study, Travel, Personal, General, Health, Gym, Shopping, Other). Active chip turns blue via `set_category()` (lines 322–330).
   - **Action Row** — "Create Task" / "Update Task" and "Cancel" buttons.

### Implementation Logic

On `on_enter()` (lines 37–54), if `self.app.modify_task_data` is set (populated by `DashboardScreen.navigate_to_edit()`), the screen enters modify mode and calls `prefill_data()` (lines 270–300) to populate all fields from the passed task tuple. Otherwise, it initialises with current date/time defaults.

When `save_task()` (lines 361–421) is invoked, it: (1) validates that the title is non-empty; (2) validates that the combined due datetime is in the future; (3) encrypts the title via `encrypt_bytes(title.encode('utf-8'), self.app.derived_key)` using AES-256-GCM (returning base64-encoded ciphertext and nonce); 

paste it here , and write this figure: Screenshot `backend/crypto.py`, lines 31–40 — shows `encrypt_bytes()` AES-GCM with random nonce generation.

(4) calls `storage.save_task()` or `storage.update_task()` with all fields; 

paste it here , and write this figure: Screenshot `backend/storage.py`, lines 320–329 — shows `save_task()` INSERT statement.

and (5) writes an audit event via `write_audit()` before navigating back to the Dashboard.

paste it here , and write this figure: Screenshot `screens/create_task_screen.py`, lines 361–390 — shows `save_task()` validation, encryption call, and branch on create vs modify mode.

### Security Considerations

Task titles are encrypted client-side before any write to the local SQLite database. Only the base64-encoded ciphertext and nonce are persisted. The encryption key (`self.app.derived_key`) exists only in process memory and is never serialised.

---

### Code Evidence

| Element | File | Function / Location | Lines |
|---|---|---|---|
| Screen entry | `screens/create_task_screen.py` | `CreateTaskScreen.on_enter()` | 37–54 |
| Form construction | `screens/create_task_screen.py` | `CreateTaskScreen.load_view()` | 56–268 |
| Pre-fill for edit | `screens/create_task_screen.py` | `CreateTaskScreen.prefill_data()` | 270–300 |
| Priority selector | `screens/create_task_screen.py` | `CreateTaskScreen.set_priority()` | 302–320 |
| Category selector | `screens/create_task_screen.py` | `CreateTaskScreen.set_category()` | 322–330 |
| Save handler | `screens/create_task_screen.py` | `CreateTaskScreen.save_task()` | 361–421 |
| Title encryption | `backend/crypto.py` | `encrypt_bytes()` | 31–40 |
| Save to DB | `backend/storage.py` | `save_task()` | 320–329 |
| Update in DB | `backend/storage.py` | `update_task()` | 331–339 |
| Audit write | `backend/audit.py` | `write_audit()` | — |

---

---

**Testing Note:** For technical details regarding the resolution of task editing persistence failures, see **Chapter 6** documentation.

---

---

---

---

## 5.7 Analytics Screen

paste it here , and write this figure: **Figure 5.7** — Analytics Screen

This section describes the Analytics Screen, which presents a quantitative overview of the user's task management and productivity metrics. It is implemented in `screens/analytics_screen.py` via the `AnalyticsScreen` class extending `MDScreen`. Statistical data is obtained through direct SQLite queries on the local database, and AI-generated weekly insights are provided by `backend/ai_assistant.py`.

### UI Structure

The screen renders a static blue header with a date range label and a vertically scrollable content area built asynchronously. The content comprises:

1. **Summary Cards Row** — A horizontally scrollable row of six 100×100dp `MDCard` tiles: Total Tasks, Completed, Pending, Upcoming, Completion Rate (%), High Priority.
2. **Weekly Progress Bar Chart** — An `MDCard` with a custom bar chart rendered as proportional `MDBoxLayout` vertical bars (one per day, Mon–Sun). Navigation arrows (`prev_week()` / `next_week()`) shift the viewing window by week offset.

paste it here , and write this figure: Screenshot lines 292–329 — shows `render_chart_bars()` building the proportional bar chart.

3. **Priority Distribution Row** — Three `MDCard` tiles for High (red), Medium (yellow), Low (green) priority completed-task counts.
4. **AI Insight Card** — A tappable `ClickableCard` displaying a `robot` icon and a generated textual performance summary.

### Implementation Logic

On `on_enter()` (lines 48–54), `load_view()` initialises the layout and launches `bg_fetch_data()` on a background daemon thread via `threading.Thread` (line 79–79). This function calls `calculate_overall_stats()` (lines 331–410) and `calculate_weekly_stats()` (lines 412–436), both of which open a direct SQLite connection via `sqlite3.connect(self.app.db_path)` and execute scoped `SELECT COUNT(*)` queries. Upon completion, `Clock.schedule_once()` defers `update_ui_with_data()` back to the Kivy main thread to satisfy Kivy's single-threaded rendering constraint.

paste it here , and write this figure: Screenshot `screens/analytics_screen.py`, lines 115–124 — shows the background thread launch and `Clock.schedule_once()` deferred callback.

`calculate_overall_stats()` scopes all queries to the current Monday–Sunday week boundary, computing total tasks created, completed, pending (past due and not completed), upcoming (future and not completed), and the weekly completion rate as `completed / (completed + week_pending)`. Priority distribution queries filter by both `priority` and `completed_iso` within the current week.

paste it here , and write this figure: Screenshot lines 331–370 — shows `calculate_overall_stats()` SQL queries with week boundary scoping.

---

### Code Evidence

| Element | File | Function / Location | Lines |
|---|---|---|---|
| Screen entry | `screens/analytics_screen.py` | `AnalyticsScreen.on_enter()` | 48–54 |
| Layout build | `screens/analytics_screen.py` | `AnalyticsScreen.load_view()` | 56–79 |
| Background fetch | `screens/analytics_screen.py` | `AnalyticsScreen.bg_fetch_data()` | 115–124 |
| Weekly stats | `screens/analytics_screen.py` | `AnalyticsScreen.calculate_weekly_stats()` | 412–436 |
| Overall stats | `screens/analytics_screen.py` | `AnalyticsScreen.calculate_overall_stats()` | 331–410 |
| UI update (main thread) | `screens/analytics_screen.py` | `AnalyticsScreen.update_ui_with_data()` | 131–229 |
| Bar chart render | `screens/analytics_screen.py` | `AnalyticsScreen.render_chart_bars()` | 292–329 |
| AI insight | `backend/ai_assistant.py` | `generate_weekly_insight()` | — |
| Database | `tasks` table | `completed_iso`, `created_iso`, `priority` columns | — |

---

---

**Testing Note:** For technical details regarding the resolution of `CalledFromWrongThread` Kivy exceptions, see **Issue 5 (Terminal TypeError Crash)** in Chapter 6 (related threading issues).

---

---

---

---

## 5.8 Settings Screen

paste it here , and write this figure: **Figure 5.8** — Settings Screen

This section describes the Settings Screen, which provides user-configurable application preferences and account security controls. It is implemented in `screens/settings_screen.py` via the `SettingsScreen` class extending `MDScreen`. It interacts with `backend/storage.py` (`save_theme_preference`, `change_passphrase`) and `backend/firebase_service.py` (`sign_in_with_email_password`, `update_password`).

### UI Structure

The screen follows the standard header-plus-scrollable-content layout. Three configurable sections are presented:

1. **Theme Toggle** — Two `MDFillRoundFlatIconButton` controls for "Light Mode" and "Dark Mode". The currently active theme is visually distinguished via background colour (`(0.8, 0.8, 0.8, 1)` for Light, `(0.3, 0.3, 0.5, 1)` for Dark).
2. **Audit Analytics Controls** — A full-width button navigating to the `AuditAnalyticsScreen`.
3. **Security Section** — A "Change Password" button opening an `MDDialog` with two masked input fields and a "Save" trigger.

### Implementation Logic

`set_theme()` (lines 142–154) applies the selected theme style to `app.theme_cls.theme_style`, calls `app.update_theme_colors()` to propagate the change globally, and persists the preference via `save_theme_preference(style, app.storage_path)` for restoration on the next launch.

`do_change_pass()` (lines 203–273) executes: (1) retrieves the user's email from Firestore via `get_username_data()`; (2) verifies the old passphrase against Firebase Authentication via `sign_in_with_email_password()`; (3) invokes `update_password(id_token, new_password)` to update the Firebase Authentication credential. A success dialog confirms completion. Any error at any step halts the workflow and surfaces a descriptive error dialog.

paste it here , and write this figure: Screenshot `screens/settings_screen.py`, lines 233–252 — shows Firebase re-authentication and password update calls.

### Security Considerations

No password value is stored or logged at any point. Transmission occurs only over HTTPS to the Firebase Authentication REST API. 

paste it here , and write this figure: Screenshot `backend/firebase_service.py`, lines 108–130 — shows `update_password()`.

The local PBKDF2-derived encryption key is unaffected by a Firebase password change; the user must re-authenticate with the new passphrase on the next session for the key to be re-derived.

---

### Code Evidence

| Element | File | Function / Location | Lines |
|---|---|---|---|
| Layout build | `screens/settings_screen.py` | `SettingsScreen.load_view()` | 28–140 |
| Theme apply | `screens/settings_screen.py` | `SettingsScreen.set_theme()` | 142–154 |
| Change password dialog | `screens/settings_screen.py` | `SettingsScreen.show_change_pass_dialog()` | 156–185 |
| Password change flow | `screens/settings_screen.py` | `SettingsScreen.do_change_pass()` | 203–273 |
| Firebase re-auth | `backend/firebase_service.py` | `sign_in_with_email_password()` | 39–62 |
| Firebase pw update | `backend/firebase_service.py` | `update_password()` | 108–130 |
| Theme persistence | `backend/storage.py` | `save_theme_preference()` | — |

---

---

**Testing Note:** For technical details regarding the resolution of password update race conditions, see **Chapter 6** documentation.

---

---

---

## 5.9 Audit Analytics Screen

paste it here , and write this figure: **Figure 5.9** — Audit Analytics Screen

This section describes the Audit Analytics Screen, which presents a time-windowed view of notification delivery and task interaction events recorded in the local audit log. 

paste it here , and write this figure: Screenshot lines 173–182 — shows the `CREATE TABLE audit` DDL with all column definitions.

It is implemented in `screens/audit_analytics_screen.py` via the `AuditAnalyticsScreen` class extending `MDScreen`. Data is obtained from `backend/storage.py` via `get_audit_stats()`.

### UI Structure

The screen header maintains the global blue card design language. The scrollable content area includes:

1. **Date Navigation** — Left and right chevron `MDIconButton` controls adjusting `offset_days` and a date range label.
2. **Notification Metrics** — Cards showing counts for notifications sent, opened, and snoozed.
3. **Task Lifecycle Metrics** — Cards for tasks created and completed in the window.
4. **Average Response Time** — Mean time (in minutes) between notification dispatch and user acknowledgement.
5. **Audit Timeline** — A scrollable list of raw audit events with event type, task ID, and ISO timestamp.

### Implementation Logic

`get_audit_stats(db_path, days, offset_days)` in `storage.py` opens a direct SQLite connection and executes scoped `SELECT` queries against the `audit` table bounded by `timestamp_iso >= start_iso AND timestamp_iso < end_iso`. Average response time is computed by pairing `"notified"` and `"dismissed"` events sharing the same `task_id`. Navigation buttons adjust `offset_days` and trigger a UI refresh cycle.

paste it here , and write this figure: Screenshot `backend/storage.py`, lines 412–470 — shows `get_audit_stats()` SQL queries and date range construction.

---

### Code Evidence

| Element | File | Function / Location | Lines |
|---|---|---|---|
| Stats retrieval | `backend/storage.py` | `get_audit_stats()` | 412–520 |
| Audit table | `backend/storage.py` | `CREATE TABLE audit` | 173–182 |
| Audit write | `backend/audit.py` | `write_audit()` | — |
| Database columns | `audit` table | `task_id`, `event`, `timestamp_iso`, `user_uid` | — |

---

---

**Testing Note:** For technical details regarding the resolution of audit response time calculations, see **Issue 6 (Audit Sync)** in Chapter 6.

---

---

---

---

## 5.10 Calendar Screen

paste it here , and write this figure: **Figure 5.10** — Calendar Screen

This section describes the Calendar Screen, which provides a month-grid view of the user's scheduled tasks. The implementation is split across `screens/calendar_month_screen.py` (`CalendarMonthScreen`) and `screens/calendar_day_screen.py` (`CalendarDayScreen`). Both screens interact with `backend/storage.py` (`list_tasks`) and `backend/crypto.py` (`decrypt_bytes`).

### UI Structure

**Month View:** A 7-column `MDGridLayout` renders the calendar month grid. Each day cell displays the day number; cells with tasks show an accent dot indicator. Navigation arrows shift the viewed month.

**Day View:** A vertically scrollable task list filtered to the selected date, rendered as simplified task cards with title (decrypted), time, and priority colour indicator. A back arrow returns to the month view.

### Implementation Logic

On entering the Month View, `list_tasks()` retrieves all tasks and their `due_iso` values. 

paste it here , and write this figure: Screenshot `backend/storage.py`, lines 341–350 — shows `list_tasks()` SELECT query.

A `date → task_count` dict is built by parsing the date component of each `due_iso`. This dict drives the dot indicators per calendar cell. 

paste it here , and write this figure: Screenshot `screens/calendar_month_screen.py` — shows `build_calendar()` grid construction and weekday offset logic.

Selecting a day passes the date to the Day View, which re-queries or filters the task list, decrypts each title, and renders the results.

paste it here , and write this figure: Screenshot `screens/calendar_day_screen.py` — shows `load_tasks()` fetching and decrypting tasks for the selected date.

---

### Code Evidence

| Element | File | Function / Location | Lines |
|---|---|---|---|
| Month grid render | `screens/calendar_month_screen.py` | `CalendarMonthScreen.build_calendar()` | — |
| Day task list | `screens/calendar_day_screen.py` | `CalendarDayScreen.load_tasks()` | — |
| Task fetch | `backend/storage.py` | `list_tasks()` | 341–350 |
| Title decrypt | `backend/crypto.py` | `decrypt_bytes()` | 42–51 |

---

---

**Testing Note:** For technical details regarding the resolution of Android calendar grid displacement, see **Chapter 6** documentation.

---

---

---

---

## 5.11 Background Scheduler and Notification System

paste it here , and write this figure: **Figure 5.11** — Notification Scheduler

This section describes the background scheduler component, which is responsible for polling the local task database at regular intervals and triggering system notifications when tasks become due. It is implemented in `backend/scheduler.py` via the `Scheduler` class, which extends `threading.Thread`. System notifications are delivered via `plyer.notification` and the in-app callback is handled by `utils/notification_manager.py`.

### Implementation Logic

`Scheduler.__init__()` (lines 47–73) accepts the database path, the derived encryption key, and an `on_notify_callback`. It establishes a scheduler-specific file logger (`_setup_scheduler_logger()`, lines 32–42) writing to the same directory as the user database, ensuring logs are written to a writable location in both development and packaged builds.

paste it here , and write this figure: Screenshot `backend/scheduler.py`, lines 32–42 — shows `_setup_scheduler_logger()` writing to `db_path` directory.

`Scheduler.run()` (lines 75–165) executes a polling loop that wakes every `POLL_INTERVAL` seconds (10s in development). 

paste it here , and write this figure: Screenshot lines 75–100 — shows the polling loop, row unpacking, and `due <= now` comparison.

Each iteration: (1) retrieves all task rows via `list_tasks()`; (2) unpacks each row according to its column count (8–12 columns, depending on schema version); (3) skips tasks already marked `notified=1` or `notified=2`, or already completed; (4) compares `due_iso` (parsed as local naive datetime) against `datetime.now()`; (5) for overdue tasks, decrypts the title via `decrypt_bytes()`, marks the task as notified via `mark_notified()`, and invokes `on_notify_callback(task_id, title)`. The callback triggers `NotificationManager.show_alert()` in `utils/notification_manager.py`, which calls `plyer.notification.notify()` for a system OS notification banner.

paste it here , and write this figure: Screenshot lines 140–152 — shows `mark_notified()` call and `on_notify` callback invocation.

---

### Code Evidence

| Element | File | Function / Location | Lines |
|---|---|---|---|
| Logger setup | `backend/scheduler.py` | `_setup_scheduler_logger()` | 32–42 |
| Scheduler class | `backend/scheduler.py` | `Scheduler.__init__()` | 47–73 |
| Polling loop | `backend/scheduler.py` | `Scheduler.run()` | 75–165 |
| Row unpacking | `backend/scheduler.py` | `run()`, if/elif chain | 84–98 |
| Notify mark | `backend/storage.py` | `mark_notified()` | 352–358 |
| OS notification | `utils/notification_manager.py` | `NotificationManager.show_alert()` | — |
| plyer import | `backend/scheduler.py` | top-level try/except | 10–13 |
| POLL_INTERVAL | `backend/scheduler.py` | module constant | 30 |

---

---

**Testing Note:** For technical details regarding logging and scheduler lifecycle failures on Android and Windows, see **Issue 1 (Android Startup Crash)** and **Issue 5 (Terminal TypeError Crash)** in Chapter 6.

---

---

---

## 5.12 Encryption Module

paste it here , and write this figure: **Figure 5.12** — Cryptographic Architecture

This section describes the cryptographic subsystem of the RemindMe application. All encryption logic is centralised in `backend/crypto.py`. 

paste it here , and write this figure: Screenshot `backend/crypto.py`, entire file (lines 1–51) — shows all cryptographic primitives: `gen_salt()`, `derive_key()`, `encrypt_bytes()`, `decrypt_bytes()`.

The module provides salt generation, key derivation, and symmetric encryption and decryption operations using the PyCryptodome library.

### Implementation Logic

`gen_salt()` (line 11–12) generates a 16-byte cryptographically random salt using `get_random_bytes(16)` from PyCryptodome's `Crypto.Random` module.

`derive_key(passphrase, salt)` (lines 27–29) applies PBKDF2-HMAC-SHA256 with 200,000 iterations (`ITERATIONS = 200_000`, line 8) and a 256-bit output length (`KEY_LEN = 32`, line 9) to produce the user's encryption key from a seedstring of the form `"{username}:{email}"` and the stored salt.

paste it here , and write this figure: Screenshot line 8–9 — highlight `ITERATIONS = 200_000` and `KEY_LEN = 32` constants.

`encrypt_bytes(plaintext, key)` (lines 31–40) generates a 12-byte random nonce (`get_random_bytes(12)`), initialises an AES cipher in GCM mode, encrypts the plaintext, and appends the 16-byte authentication tag to the ciphertext. The concatenated ciphertext+tag and the nonce are returned as base64-encoded strings for safe database storage.

`decrypt_bytes(ct_b64, nonce_b64, key)` (lines 42–51) decodes the base64 inputs, splits the final 16 bytes as the GCM authentication tag, initialises an AES-GCM cipher with the nonce, and calls `decrypt_and_verify()`. This operation authenticates and decrypts simultaneously — any tampering with the ciphertext or use of an incorrect key causes a `ValueError` to be raised.

---

### Code Evidence

| Element | File | Function | Lines |
|---|---|---|---|
| Salt generation | `backend/crypto.py` | `gen_salt()` | 11–12 |
| KDF parameters | `backend/crypto.py` | Module constants `ITERATIONS`, `KEY_LEN` | 8–9 |
| Key derivation | `backend/crypto.py` | `derive_key()` | 27–29 |
| Encryption | `backend/crypto.py` | `encrypt_bytes()` | 31–40 |
| Decryption + verify | `backend/crypto.py` | `decrypt_bytes()` | 42–51 |
| Salt persistence | `backend/crypto.py` | `save_salt_for()` | 14–18 |
| Salt loading | `backend/crypto.py` | `load_salt_for()` | 20–25 |
| Usage (task encrypt) | `screens/create_task_screen.py` | `CreateTaskScreen.save_task()` | 388 |
| Usage (task decrypt) | `screens/dashboard_screen.py` | `DashboardScreen.refresh_tasks()` | 353 |

---

---

**Testing Note:** For technical details regarding the resolution of cryptographic salt corruption and AES-GCM tag verification failures, see **Chapter 6** documentation.

---

---

---

## 5.13 Security and System Integration Overview

This section summarises the security design principles and cross-component integration patterns applied throughout the RemindMe application.

### Cryptographic Architecture

All user task data is encrypted client-side using AES-256-GCM before being written to the local SQLite database. The encryption key is never stored — it is re-derived on each login session from the user's passphrase using PBKDF2-HMAC-SHA256 (200,000 iterations) combined with a per-user 16-byte random salt. The salt and wrapped Data Encryption Key (DEK) are stored in Firebase Firestore, while the plaintext key exists only in process memory for the duration of the authenticated session.

Authentication is handled exclusively by Firebase Authentication via HTTPS. The application never transmits or stores plaintext passwords. Password change operations require re-authentication with the existing credential before the Firebase token is updated.

### Cross-Component Integration

The application integrates four distinct backend subsystems:

| Subsystem | Module | Role |
|---|---|---|
| Firebase Authentication | `backend/firebase_service.py` | User sign-in, sign-up, password reset |
| Cloud metadata store | Firebase Firestore | Username→UID mapping, salt, wrapped DEK |
| Local encrypted database | `backend/storage.py` + SQLite | Task data, audit log, theme preference |
| Background notification engine | `backend/scheduler.py` + `utils/notification_manager.py` | Due-date polling, OS notification delivery |

The `main.py` `ReminderApp` class acts as the integration hub: it holds the in-memory derived key (`app.derived_key`), the database file path (`app.db_path`), and the current user identity. Screens communicate with each other exclusively through these shared application properties and the `ScreenManager` transition API, avoiding direct screen-to-screen imports.

### Platform Handling

The application targets both Windows (packaged as a PyInstaller `.exe`) and Android (packaged via Buildozer). Platform-specific branches are isolated to `utils/notification_manager.py` (win10toast on Windows, plyer+channel on Android) and `utils/helpers.py` (`get_storage_path()` / `get_asset_path()`). All other application logic is platform-agnostic.

---

## 5.14 Chapter Summary

Chapter 5 documented the complete system implementation of the RemindMe application across fourteen components: the Welcome Screen, Login and Registration, Forgot Password, Dashboard, Create Task, Analytics, Settings, Audit Analytics, Calendar, Background Scheduler, Encryption Module, Security Architecture, and this summary.

Each section presented the UI structure, implementation logic, supporting code evidence table, a development challenge with its root cause and fix, and screenshot guidance for submission. Key technical outcomes achieved during implementation include:

- **End-to-end task encryption** using AES-256-GCM with per-session key derivation, ensuring all user task titles are protected at rest.
- **Cross-platform notification delivery** via win10toast (Windows) and plyer with notification channels (Android), with thread-safe dispatch through Kivy's `Clock.schedule_once`.
- **Stable Android packaging** achieved by correcting the Buildozer configuration: removing the invalid `services=` directive, upgrading `android.api` to 33, adding the missing `dateparser` dependency, and correcting the `package.name` to eliminate APK install failures.
- **Robust background scheduler** implemented as a daemon thread with configurable polling interval, per-row schema-adaptive unpacking, and database-co-located log output.
- **Firestore-aligned authentication** ensuring that the write path (registration) and read path (login) both target the same Firestore `users` collection, eliminating the initial login failure caused by a Realtime Database/Firestore endpoint mismatch.

The implemented system meets all functional requirements outlined in Chapter 3 and the design specifications documented in Chapter 4, providing a secure, cross-platform task reminder application with cloud-backed authentication and local encrypted storage.

---

*End of Chapter 5 — System Implementation*
