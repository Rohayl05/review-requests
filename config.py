import os
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_PHONE_NUMBER = os.environ["TWILIO_PHONE_NUMBER"]
BUSINESS_OWNER_NUMBER = os.environ["BUSINESS_OWNER_NUMBER"]
BUSINESS_REVIEW_LINK = os.environ.get("BUSINESS_REVIEW_LINK", "")

# Booking page branding
BUSINESS_NAME = os.environ.get("BUSINESS_NAME", "Your Trades Business")
BUSINESS_TAGLINE = os.environ.get("BUSINESS_TAGLINE", "Fast, reliable, local.")

# Owner dashboard auth (password only; any username accepted)
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "")

# Review timing: sent the NEXT day at this hour, UK local time (BST-aware).
REVIEW_SEND_HOUR = int(os.environ.get("REVIEW_SEND_HOUR", "10"))  # 10:00 UK

# SMS templates — edit per client
REVIEW_REQUEST_MESSAGE = (
    "Hi {name}, thanks for choosing us! We hope everything went smoothly. "
    "If you have a moment, we'd really appreciate a quick review: {review_link}"
)

# SMS the owner gets when a customer submits the booking form
NEW_BOOKING_MESSAGE = (
    "New booking \U0001F6E0\n"
    "Name: {name}\n"
    "Phone: {phone}\n"
    "Address: {address}\n"
    "Details: {details}"
)
