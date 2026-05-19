Mailtrap + Supabase setup (development)

Overview

This document explains how to configure Mailtrap as your SMTP provider for Supabase Authentication (development only) and how to verify the password recovery flow end-to-end.

1) Create a Mailtrap inbox

- Sign up at https://mailtrap.io (free dev tier available).
- Create an Inbox and copy its SMTP credentials (host, port, username, password).

2) Update `backend_api/.env`

Open `backend_api/.env` and replace the `MAILTRAP_*` placeholders with the values from your Mailtrap inbox. Example:

MAILTRAP_SMTP_HOST=smtp.mailtrap.io
MAILTRAP_SMTP_PORT=587
MAILTRAP_SMTP_USERNAME=0123456789abcdef
MAILTRAP_SMTP_PASSWORD=abcdef0123456789
MAILTRAP_SENDER_EMAIL=remindme-dev@example.com

3) Configure Supabase Authentication Email Provider

- Open your Supabase project dashboard.
- Navigate to Authentication -> Settings -> Email.
- Set the SMTP host, port, username, password using the Mailtrap values.
- Set "Sender email" to the `MAILTRAP_SENDER_EMAIL` value used above.
- Save settings.

4) Add Redirect URLs

In Supabase Authentication -> Settings -> Redirect URLs (or Site URL / Redirects), add these entries:

- http://localhost:3000/reset-password
- http://10.0.2.2:3000/reset-password
- remindme://reset-password

These must be saved in the Supabase project for the `redirect_to` used by the backend to be allowed.

5) Restart the backend

From the repo root run (PowerShell):

```powershell
.\run_backend.ps1
```

6) Trigger and verify the password recovery flow

A quick local test:

- Create a test account (sign up) using the app or API.
- In the app, open the Reset Password flow and enter the account's email.
- Mailtrap inbox: open your Mailtrap inbox, you should see the recovery email arrive.
- Click the recovery link in the email (it will contain the Supabase recovery token and a `redirect_to` URL).
- Complete the reset page (your frontend should capture the token and call the backend `confirm-password-reset` endpoint or use the Supabase flow).
- Sign in with the new password.

7) Notes on automation

- If you want fully automated verification, Mailtrap provides an API to fetch messages; you would need to provide the inbox API token. I did NOT implement any dev bypass and will not add fake reset logic.

8) Troubleshooting

- If recovery still fails, check these logs:
  - `backend_errors.log` (production-style errors)
  - `auth_debug.log` (detailed supabase/auth trace output)

- Make sure the Redirect URLs listed in step (4) are saved in Supabase exactly as provided.
- Ensure SMTP credentials are correct and Mailtrap inbox is active.

9) After successful dev verification

- Replace Supabase SMTP with your production provider (SendGrid, etc.).
- Remove Mailtrap credentials from any shared place and rotate keys if needed.

