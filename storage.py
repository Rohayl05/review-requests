import json
import os
import uuid
from datetime import datetime, timezone

REVIEW_REQUESTS_FILE = "review_requests.json"
BOOKINGS_FILE = "bookings.json"


def _read(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)


def _write(path: str, data: list) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def log_review_request(customer_number: str, customer_name: str, scheduled_at: str) -> None:
    records = _read(REVIEW_REQUESTS_FILE)
    records.append({
        "customer_number": customer_number,
        "customer_name": customer_name,
        "scheduled_at": scheduled_at,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    _write(REVIEW_REQUESTS_FILE, records)


def log_booking(name: str, phone: str, address: str, details: str) -> dict:
    records = _read(BOOKINGS_FILE)
    booking = {
        "id": uuid.uuid4().hex[:8],
        "name": name,
        "phone": phone,
        "address": address,
        "details": details,
        "status": "new",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "review_scheduled_at": None,
    }
    records.append(booking)
    _write(BOOKINGS_FILE, records)
    return booking


def get_bookings() -> list:
    return _read(BOOKINGS_FILE)


def approve_booking(booking_id: str, review_scheduled_at: str) -> dict | None:
    records = _read(BOOKINGS_FILE)
    for b in records:
        if b["id"] == booking_id and b["status"] == "new":
            b["status"] = "approved"
            b["review_scheduled_at"] = review_scheduled_at
            _write(BOOKINGS_FILE, records)
            return b
    return None


def get_pending_reviews() -> list:
    """Approved bookings whose review time is still in the future (for startup re-hydration)."""
    now = datetime.now(timezone.utc).isoformat()
    return [
        b for b in _read(BOOKINGS_FILE)
        if b["status"] == "approved" and (b.get("review_scheduled_at") or "") > now
    ]
