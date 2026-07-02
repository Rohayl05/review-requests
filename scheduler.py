from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
import config
import twilio_helpers
import storage

scheduler = BackgroundScheduler(timezone="UTC")

# Review send times are reasoned about in UK local time so REVIEW_SEND_HOUR
# means the same wall-clock hour year-round (handles BST automatically).
_UK_TZ = ZoneInfo("Europe/London")


def _send_review_sms(customer_number: str, customer_name: str) -> None:
    body = config.REVIEW_REQUEST_MESSAGE.format(
        name=customer_name,
        review_link=config.BUSINESS_REVIEW_LINK,
    )
    twilio_helpers.send_sms(to=customer_number, body=body)


def _next_day_send_time() -> datetime:
    """Tomorrow at REVIEW_SEND_HOUR UK local time, returned as a UTC datetime."""
    target_uk = (datetime.now(_UK_TZ) + timedelta(days=1)).replace(
        hour=config.REVIEW_SEND_HOUR, minute=0, second=0, microsecond=0
    )
    return target_uk.astimezone(timezone.utc)


def schedule_review(customer_number: str, customer_name: str) -> str:
    """Schedule a review SMS for the next day at REVIEW_SEND_HOUR. Returns ISO run time."""
    run_at = _next_day_send_time()
    scheduler.add_job(
        _send_review_sms,
        trigger="date",
        run_date=run_at,
        args=[customer_number, customer_name],
        misfire_grace_time=3600,
    )
    storage.log_review_request(
        customer_number=customer_number,
        customer_name=customer_name,
        scheduled_at=run_at.isoformat(),
    )
    return run_at.isoformat()


def reschedule_pending_reviews() -> None:
    """On startup, re-add jobs for approved bookings whose review hasn't fired yet."""
    for b in storage.get_pending_reviews():
        scheduler.add_job(
            _send_review_sms,
            trigger="date",
            run_date=datetime.fromisoformat(b["review_scheduled_at"]),
            args=[b["phone"], b["name"]],
            misfire_grace_time=3600,
        )
