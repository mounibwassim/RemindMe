# Production Email Setup Guide for Transactional OTP Delivery

This guide outlines the best free and low-cost email delivery solutions to send 6-digit OTP codes to any recipient from the **Render-hosted backend** without changing the existing OTP workflow or Dart client code.

---

## 📊 Comparison of Production Solutions

| Provider | Authentication Type | Monthly Cost | Sending Limits | Render Compatibility | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Resend (Verified Domain)** | HTTP REST API | **$0** (Free Tier) | 3,000 / month<br>(100 / day) | 100% Compatible | **Highly Recommended** (Zero code changes, zero cost, premium inbox delivery) |
| **Brevo (formerly Sendinblue)** | HTTP REST API | **$0** (Free Tier) | 9,000 / month<br>(300 / day) | 100% Compatible | **Excellent Alternative** (No domain verification required, high limits) |
| **Amazon SES** | HTTP API or SMTP | **$0.10** per 1,000 emails | Virtually Unlimited | 100% Compatible (via SDK) | Good for enterprise scaling, but complex setup |
| **SendGrid** | HTTP REST API | **$0** (Free Tier) | 3,000 / month<br>(100 / day) | 100% Compatible | Decent, but strict limits |
| **Supabase SMTP** | Built-in Auth SMTP | N/A | 3 / hour (default) | Not Compatible | **Not Compatible** (Can only send built-in Supabase links, not custom database OTPs) |
| **Gmail SMTP** | SMTP Port 587/465 | **$0** (Personal) | 500 / day | **Blocked on Render** | **Not Compatible** (Render blocks outgoing SMTP ports) |

---

## 🏆 Recommended Solution 1: Verified Resend Domain (Free Tier)
Since the backend already has Resend integrated, you only need to verify a custom domain on your Resend dashboard. This unlocks sending to **any recipient domain** with **zero code modifications**.

### Cost:
* **Resend Account:** $0/month.
* **Domain Name:** ~$1 to $3/year (buy a cheap domain like `.xyz`, `.club`, `.site`, or `.icu` from Namecheap or Cloudflare).

### Setup Steps:
1. **Buy a Cheap Domain:**
   * Go to a registrar (e.g., [Namecheap](https://www.namecheap.com/) or [Cloudflare Registrar](https://www.cloudflare.com/products/registrar/)).
   * Purchase a low-cost domain (e.g., `remindme-project.xyz` for ~$1.50).
2. **Add Domain to Resend:**
   * Log into [Resend](https://resend.com/).
   * Navigate to **Domains** -> **Add Domain**.
   * Enter your domain name and select your hosting region.
3. **Configure DNS Records:**
   * Resend will provide 3 DKIM/SPF DNS records (TXT/MX/CNAME).
   * Go to your registrar's DNS dashboard (e.g. Advanced DNS on Namecheap) and add these records.
   * Wait a few minutes and click **Verify** on Resend until the status changes to **Verified**.
4. **Configure Render Environment Variables:**
   * Log into your **Render Dashboard**.
   * Select your web service (`remindme-backend`).
   * Go to **Environment** and set/update:
     * `RESEND_FROM_EMAIL=recovery@yourdomain.xyz` (replace with your verified domain).
5. **Test the Flow:**
   * Trigger the forgot-password flow in the app.
   * The recipient will now receive the recovery email directly in their inbox!

## 🚫 Sandbox Redirection Status
All sandbox redirection logic has been completely removed from the backend. The backend now attempts direct delivery to the recipient's email address. To send emails to any recipient in production, you must use a verified Resend domain or Brevo HTTP API.

---

## 🥈 Recommended Solution 2: Brevo HTTP API (Free Tier)
If you do not want to purchase a domain name, **Brevo** is the best alternative. It allows sending up to **300 emails per day completely free** using a single verified sender email (e.g. your personal Gmail). 

The backend code for Brevo is already fully written in `backend/email_service.py`!

### Cost:
* **Brevo Account:** $0/month.
* **Domain Name:** $0 (supports single sender verification using your existing personal Gmail).

### Setup Steps:
1. **Create a Free Brevo Account:**
   * Sign up at [Brevo](https://www.brevo.com/).
2. **Configure Sender:**
   * Go to **Senders & IPs** -> **Senders** -> **Add a sender**.
   * Enter your name and sender email address (e.g., `yourname@gmail.com`).
   * Confirm the email address by clicking the link sent to your inbox.
3. **Get API Key:**
   * Navigate to **SMTP & API** -> **API Keys**.
   * Create a new API key and copy it.
4. **Configure Render Environment Variables:**
   * Go to your **Render Dashboard** for your web service.
   * Add the following environment variables:
     * `BREVO_API_KEY=your_brevo_api_key`
     * `SENDER_EMAIL=yourname@gmail.com` (must match the verified sender in Brevo).
5. **Why this works immediately:**
   * The backend prioritizes Brevo if `BREVO_API_KEY` is configured. It calls `https://api.brevo.com/v3/smtp/email` via HTTP POST, which bypasses Render's SMTP block and delivers to any inbox.
