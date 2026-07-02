## Project Overview
A FastAPI service for UK trades businesses (plumbers, electricians etc)
that handles the customer-facing booking flow and post-job review
requests:
1. Booking form (/book): a shareable mobile page where customers submit
   their details; the owner is texted instantly and the booking is logged.
2. Owner dashboard (/dashboard): password-protected page listing new
   bookings and scheduled reviews.
3. Approval-driven review requests: the owner approves a finished job on
   the dashboard, and the customer gets a review-request SMS the next day
   at REVIEW_SEND_HOUR (UK local time). The legacy /job-complete API still
   works.

This service is one half of a two-service split. The missed-call
auto-text-back feature lives in the sibling **missed-call-textback**
project/repo — this service does not handle inbound calls at all.

## Tech Stack
- Python 3.11
- FastAPI + uvicorn
- Twilio Python SDK (SMS)
- APScheduler (delayed review SMS)
- python-dotenv for env vars
- Fly.io for hosting
- JSON file storage (review_requests.json, bookings.json) — structured to
  be swappable for a DB later

## Project Structure
/
├── main.py
├── config.py
├── scheduler.py
├── storage.py
├── twilio_helpers.py
├── templates.py         # server-rendered HTML (no template engine)
├── requirements.txt
├── Dockerfile
├── .env.example
├── .gitignore
└── CLAUDE.md

## Environment Variables
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
BUSINESS_OWNER_NUMBER=
BUSINESS_REVIEW_LINK=
BUSINESS_NAME=
BUSINESS_TAGLINE=
DASHBOARD_PASSWORD=
REVIEW_SEND_HOUR=        # hour (UK local time) the next-day review SMS is sent; default 10

## Endpoints
GET  /book          → mobile booking form for customers
POST /book          → log booking, text details to owner
GET  /dashboard      → owner dashboard (HTTP Basic, password = DASHBOARD_PASSWORD)
POST /approve        → approve a booking, schedule next-day review SMS (auth)
POST /job-complete   → legacy API: schedules a next-day review SMS

## Config Design
All business-specific values (message templates, links) live in config.py
so this can be customized per client later.

## Key Constraints
- No database — JSON file storage only (MVP). Dashboard uses simple HTTP
  Basic auth (password only); customer-facing pages are server-rendered HTML.
- Must work end-to-end locally via ngrok (or plain localhost, since this
  service has no inbound Twilio webhooks) before deploying to Fly.io
- README must include: local setup, testing steps, Fly.io deploy steps
- .env must never be committed

## Gotchas — read before changing review/scheduling code
- Scheduled reviews live in-memory (APScheduler), so they do NOT survive a
  restart on their own. `scheduler.reschedule_pending_reviews()` runs on
  startup and re-adds jobs from APPROVED bookings in bookings.json.
  IMPORTANT GAP: reviews scheduled via the legacy `/job-complete` path are
  only logged to review_requests.json (no booking record) and are NOT
  re-hydrated — a restart loses them. Prefer the dashboard approve flow.
- JSON storage is ephemeral on Fly.io: the container filesystem resets on
  every redeploy, so bookings.json / review_requests.json are wiped. Fine
  for a demo; needs a Fly volume or DB for production.
- REVIEW_SEND_HOUR is UK local time (Europe/London, BST-aware): scheduler.py
  computes the next-day send moment in UK time then converts to UTC for
  APScheduler. Stored review_scheduled_at / dashboard display is still UTC, so
  in summer a 10:00 UK send shows as 09:00 UTC — that's correct, not a bug.
  Requires the tzdata package (in requirements.txt) for zoneinfo on Windows.
- Customer-entered phone numbers are normalized to E.164 via
  twilio_helpers.to_e164() at the /book and /job-complete boundaries (UK "0..."
  -> "+44..."), so Twilio can actually deliver.
- Dashboard auth fails closed: an empty DASHBOARD_PASSWORD denies all
  /dashboard and /approve access. It is password-only HTTP Basic (any
  username) — single-owner grade, not multi-user/role-based.
- templates.py renders raw HTML; always html.escape() any customer-supplied
  value (name/address/details) before interpolating, or you reintroduce XSS
  on the dashboard.

## Possible Next Steps
- Persist data in a real store (SQLite + Fly volume, or Postgres) so
  bookings/reviews survive redeploys and restarts.
- Re-hydrate legacy /job-complete reviews too, or unify all review
  scheduling behind booking records (single source of truth).
- Add dashboard actions: cancel a scheduled review, or mark a job "not done".
- Owner notifications beyond SMS (email / WhatsApp) on new bookings.
