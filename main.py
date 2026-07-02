import secrets

from fastapi import FastAPI, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import config
import storage
import twilio_helpers
import scheduler as sched
import templates

app = FastAPI()
security = HTTPBasic()


def require_auth(creds: HTTPBasicCredentials = Depends(security)):
    """Password-only HTTP Basic auth for the owner dashboard (any username accepted)."""
    ok = bool(config.DASHBOARD_PASSWORD) and secrets.compare_digest(
        creds.password, config.DASHBOARD_PASSWORD
    )
    if not ok:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )


@app.on_event("startup")
def startup():
    sched.scheduler.start()
    sched.reschedule_pending_reviews()


@app.on_event("shutdown")
def shutdown():
    sched.scheduler.shutdown(wait=False)


@app.post("/job-complete")
async def job_complete(
    customer_number: str = Form(...),
    customer_name: str = Form(default="there"),
):
    """Schedule a review SMS to the customer for the next day (legacy API path)."""
    run_at = sched.schedule_review(
        customer_number=twilio_helpers.to_e164(customer_number),
        customer_name=customer_name,
    )
    return {"status": "scheduled", "send_at": run_at, "customer": customer_number}


@app.get("/book", response_class=HTMLResponse)
async def book_form():
    """Mobile-first booking form for customers."""
    return HTMLResponse(content=templates.booking_form())


@app.post("/book", response_class=HTMLResponse)
async def book_submit(
    name: str = Form(...),
    phone: str = Form(...),
    address: str = Form(default=""),
    details: str = Form(default=""),
):
    """Log the booking and text the details to the owner."""
    phone = twilio_helpers.to_e164(phone)
    storage.log_booking(name=name, phone=phone, address=address, details=details)
    twilio_helpers.send_sms(
        to=config.BUSINESS_OWNER_NUMBER,
        body=config.NEW_BOOKING_MESSAGE.format(
            name=name, phone=phone, address=address or "—", details=details or "—"
        ),
    )
    return HTMLResponse(content=templates.booking_confirmation())


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(_: None = Depends(require_auth)):
    """Owner dashboard: new bookings and scheduled reviews."""
    return HTMLResponse(content=templates.dashboard(bookings=storage.get_bookings()))


@app.post("/approve")
async def approve(
    booking_id: str = Form(...),
    _: None = Depends(require_auth),
):
    """Approve a finished job and schedule its review SMS for the next day."""
    booking = next(
        (b for b in storage.get_bookings() if b["id"] == booking_id and b["status"] == "new"),
        None,
    )
    if booking is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found or already approved")
    run_at = sched.schedule_review(
        customer_number=booking["phone"],
        customer_name=booking["name"],
    )
    storage.approve_booking(booking_id, run_at)
    return RedirectResponse("/dashboard", status_code=303)
