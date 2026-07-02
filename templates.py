"""Server-rendered HTML pages (no template engine — plain f-strings).

Kept separate from main.py so the route handlers stay readable. Any value that
originates from customer input is passed through html.escape() before rendering.
"""
from html import escape

import config

# Shared styling — one inline block, no external assets (single round-trip on mobile).
_CSS = """
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f4f4f5; color: #1a1a1a; line-height: 1.5;
    padding: 1rem; display: flex; justify-content: center;
  }
  .wrap { width: 100%; max-width: 480px; }
  .card {
    background: #fff; border-radius: 12px; padding: 1.5rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07); margin-bottom: 1rem;
  }
  h1 { font-size: 1.5rem; margin-bottom: 0.25rem; }
  h2 { font-size: 1.1rem; margin-bottom: 0.75rem; }
  .tagline { color: #666; margin-bottom: 1.25rem; }
  label { display: block; font-weight: 600; font-size: 0.9rem; margin-bottom: 1rem; }
  input, textarea {
    width: 100%; margin-top: 0.35rem; padding: 0.7rem; font-size: 1rem;
    border: 1px solid #d4d4d8; border-radius: 8px; font-family: inherit;
  }
  textarea { resize: vertical; min-height: 70px; }
  button {
    width: 100%; padding: 0.85rem; font-size: 1rem; font-weight: 600;
    color: #fff; background: #e85d04; border: none; border-radius: 8px; cursor: pointer;
  }
  button:hover { background: #cf5203; }
  button.approve { background: #2e9e3f; }
  button.approve:hover { background: #277f34; }
  .item { padding: 0.75rem 0; border-top: 1px solid #eee; }
  .item:first-child { border-top: none; }
  .item .meta { color: #666; font-size: 0.85rem; }
  .approve-form { margin-top: 0.6rem; }
  .empty { color: #999; font-size: 0.9rem; padding: 0.5rem 0; }
  .badge { display: inline-block; font-size: 0.75rem; font-weight: 600;
           color: #277f34; background: #e7f6ea; padding: 0.15rem 0.5rem; border-radius: 6px; }
"""


def _page(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)}</title>
  <style>{_CSS}</style>
</head>
<body><div class="wrap">{body}</div></body>
</html>"""


def _fmt(iso: str | None) -> str:
    """Trim an ISO timestamp to 'YYYY-MM-DD HH:MM' for display."""
    if not iso:
        return "—"
    return iso[:16].replace("T", " ")


def booking_form() -> str:
    body = f"""
    <div class="card">
      <h1>{escape(config.BUSINESS_NAME)}</h1>
      <p class="tagline">{escape(config.BUSINESS_TAGLINE)}</p>
      <form method="post" action="/book">
        <label>Your name<input name="name" required></label>
        <label>Phone number<input name="phone" type="tel" required></label>
        <label>Address<input name="address"></label>
        <label>What do you need?<textarea name="details" placeholder="e.g. Leaking kitchen tap"></textarea></label>
        <button type="submit">Request booking</button>
      </form>
    </div>"""
    return _page(f"Book — {config.BUSINESS_NAME}", body)


def booking_confirmation() -> str:
    body = f"""
    <div class="card">
      <h1>Thanks! 🛠</h1>
      <p class="tagline">We've got your details and {escape(config.BUSINESS_NAME)} will be in touch shortly to confirm.</p>
    </div>"""
    return _page("Booking received", body)


def dashboard(bookings: list) -> str:
    new = [b for b in bookings if b["status"] == "new"]
    approved = [b for b in bookings if b["status"] == "approved"]

    # Newest first.
    new = new[::-1]
    approved = approved[::-1]

    if new:
        new_html = "".join(
            f"""<div class="item">
              <strong>{escape(b['name'])}</strong> — {escape(b['phone'])}
              <div class="meta">{escape(b['address'] or '—')}<br>{escape(b['details'] or '—')}</div>
              <form class="approve-form" method="post" action="/approve">
                <input type="hidden" name="booking_id" value="{escape(b['id'])}">
                <button class="approve" type="submit">✓ Approve &amp; request review</button>
              </form>
            </div>"""
            for b in new
        )
    else:
        new_html = '<div class="empty">No new bookings.</div>'

    if approved:
        approved_html = "".join(
            f"""<div class="item">
              <strong>{escape(b['name'])}</strong> — {escape(b['phone'])}
              <div class="meta"><span class="badge">Review</span> scheduled for {_fmt(b.get('review_scheduled_at'))} UTC</div>
            </div>"""
            for b in approved
        )
    else:
        approved_html = '<div class="empty">No reviews scheduled yet.</div>'

    body = f"""
    <div class="card"><h1>Dashboard</h1><p class="tagline">{escape(config.BUSINESS_NAME)}</p></div>
    <div class="card"><h2>New bookings</h2>{new_html}</div>
    <div class="card"><h2>Reviews scheduled</h2>{approved_html}</div>"""
    return _page("Dashboard", body)
