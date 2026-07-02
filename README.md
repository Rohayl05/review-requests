# review-requests

FastAPI service for UK trades businesses: a shareable mobile booking form,
a password-protected owner dashboard, and approval-driven next-day review
SMS requests.

This is one half of a two-service split. Missed-call auto-text-back lives
in the sibling **missed-call-textback** project/repo — this service has no
inbound-call webhooks.

---

## Local Setup

### 1. Clone and create a virtual environment

```bash
git clone <your-repo-url>
cd review-requests
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+441234567890
BUSINESS_OWNER_NUMBER=+447700900000
BUSINESS_REVIEW_LINK=https://g.page/r/your-review-link
BUSINESS_NAME=Dave's Plumbing
BUSINESS_TAGLINE=Fast, reliable, local plumber in Manchester
DASHBOARD_PASSWORD=change-me
REVIEW_SEND_HOUR=10
```

### 4. Run the server

```bash
uvicorn main:app --reload --port 8001
```

---

## Testing

This service has no inbound Twilio webhooks, so plain `localhost` works —
ngrok is only needed if you want to share the booking link with a real
phone before deploying.

### Test the booking → approval → review flow

1. Open `http://localhost:8001/book`, fill in the form, and submit. The owner number receives an SMS and the booking lands in `bookings.json`.
2. Open `http://localhost:8001/dashboard` (any username, password = `DASHBOARD_PASSWORD`). The booking appears under **New bookings**.
3. Click **✓ Approve & request review**. The booking moves to **Reviews scheduled** with a send time of tomorrow at `REVIEW_SEND_HOUR` UK local time (shown as UTC on the dashboard — in summer that's an hour behind, e.g. 10:00 UK = 09:00 UTC).

Customer phone numbers entered on the booking form are normalized to E.164 (UK `07…` → `+447…`) so Twilio can deliver. To verify the review SMS actually sends, temporarily set `REVIEW_SEND_HOUR` to the current UK hour and approve a booking close to that time. The legacy `POST /job-complete` API still works and schedules a next-day review too:

```bash
curl -X POST http://localhost:8001/job-complete \
  -d "customer_number=+447700900000&customer_name=John"
```

---

## Fly.io Deployment

### 1. Install flyctl and log in

```bash
# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex
fly auth login
```

### 2. Launch the app (first time only)

```bash
fly launch
```

When prompted, skip adding a database. This creates `fly.toml`.

### 3. Set secrets

```bash
fly secrets set \
  TWILIO_ACCOUNT_SID=ACxxx \
  TWILIO_AUTH_TOKEN=xxx \
  TWILIO_PHONE_NUMBER=+44xxx \
  BUSINESS_OWNER_NUMBER=+44xxx \
  BUSINESS_REVIEW_LINK=https://... \
  BUSINESS_NAME="Dave's Plumbing" \
  BUSINESS_TAGLINE="Fast, reliable, local" \
  DASHBOARD_PASSWORD=a-strong-password \
  REVIEW_SEND_HOUR=10
```

### 4. Deploy

```bash
fly deploy
```

### 5. Share the booking link

Send customers to:
```
https://<your-app>.fly.dev/book
```

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/book` | Mobile booking form for customers |
| POST | `/book` | Logs the booking and texts details to the owner |
| GET | `/dashboard` | Owner dashboard (HTTP Basic auth, password = `DASHBOARD_PASSWORD`) |
| POST | `/approve` | Approves a booking and schedules its next-day review SMS (auth) |
| POST | `/job-complete` | Legacy API — schedules a next-day review SMS (`customer_number`, `customer_name` form fields) |
