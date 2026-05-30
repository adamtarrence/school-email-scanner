"""
Lambda handler: Seasonal pause / resume reminders.

Triggered once a day by EventBridge. The pause and resume nudges are NOT
automatic actions — this function only sends emails. The actual pause/resume
happens when the parent clicks the one-click link (→ the web app's /api/pause
and /api/resume), so schedules that differ school-to-school stay under the
parent's control.

- On PAUSE_REMINDER_DATE: email active, non-paused users a "pause for the
  summer" nudge.
- On any RESUME_REMINDER_DATES: email paused users a "resume for back-to-school"
  nudge. (Two dates by default — a primary nudge and a later safety-net nudge —
  because we never auto-resume billing.)

Sends are idempotent per user per occurrence via the `reminders_sent` String
Set on the user record, so re-running on the same day sends nothing new.

Pass {"force_date": "MM-DD"} as the event to test a given calendar day without
waiting for it.
"""

import hashlib
import hmac
import os
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource("dynamodb")
ses = boto3.client("ses")

USERS_TABLE = os.environ["USERS_TABLE"]
FROM_EMAIL = os.environ.get("FROM_EMAIL", "digest@schoolskim.com")
BASE_URL = os.environ.get("BASE_URL", "https://schoolskim.com")
UNSUBSCRIBE_SECRET = os.environ.get("UNSUBSCRIBE_SECRET", "schoolskim-unsub-default")
COMPANY_ADDRESS = "SchoolSkim, 10685-B Hazelhurst Dr. #42818, Houston, TX 77043"

# MM-DD calendar markers (configurable via the SAM template).
PAUSE_REMINDER_DATE = os.environ.get("PAUSE_REMINDER_DATE", "05-12")
RESUME_REMINDER_DATES = [
    d.strip()
    for d in os.environ.get("RESUME_REMINDER_DATES", "07-28,08-25").split(",")
    if d.strip()
]


def lambda_handler(event, context):
    """Send the day's seasonal reminders, if any are scheduled for today."""
    event = event or {}
    now = datetime.now(timezone.utc)
    today = event.get("force_date") or now.strftime("%m-%d")
    year = now.year

    if today == PAUSE_REMINDER_DATE:
        kind = "pause"
        dedupe_key = f"pause:{year}"
    elif today in RESUME_REMINDER_DATES:
        kind = "resume"
        dedupe_key = f"resume:{year}:{today.replace('-', '')}"
    else:
        print(f"No seasonal reminder scheduled for {today}.")
        return {"kind": None, "sent": 0}

    users = _eligible_users(kind)
    print(f"{today}: {kind} reminder — {len(users)} candidate user(s).")

    sent = 0
    for user in users:
        user_id = user.get("user_id", "?")
        try:
            if _already_sent(user, dedupe_key):
                continue
            _send_reminder(user, kind)
            _mark_sent(user_id, dedupe_key)
            sent += 1
        except Exception as e:
            print(f"Error sending {kind} reminder to {user_id}: {e}")

    print(f"{today}: sent {sent} {kind} reminder(s).")
    return {"kind": kind, "date": today, "sent": sent}


# ── User selection ──


def _eligible_users(kind: str) -> list[dict]:
    """Active users to nudge: non-paused for 'pause', paused for 'resume'."""
    table = dynamodb.Table(USERS_TABLE)
    if kind == "pause":
        flt = Attr("status").ne("inactive") & Attr("paused").ne(True)
    else:  # resume
        flt = Attr("status").ne("inactive") & Attr("paused").eq(True)

    items: list[dict] = []
    resp = table.scan(FilterExpression=flt)
    items.extend(resp.get("Items", []))
    while "LastEvaluatedKey" in resp:
        resp = table.scan(
            FilterExpression=flt, ExclusiveStartKey=resp["LastEvaluatedKey"]
        )
        items.extend(resp.get("Items", []))
    return items


def _already_sent(user: dict, dedupe_key: str) -> bool:
    """True if this exact reminder occurrence was already sent to the user."""
    sent = user.get("reminders_sent")
    if not sent:
        return False
    return dedupe_key in sent  # boto3 returns a DynamoDB String Set as a set


def _mark_sent(user_id: str, dedupe_key: str) -> None:
    table = dynamodb.Table(USERS_TABLE)
    table.update_item(
        Key={"user_id": user_id},
        UpdateExpression="ADD reminders_sent :k",
        ExpressionAttributeValues={":k": {dedupe_key}},  # Python set → String Set
    )


# ── Sending ──


def _send_reminder(user: dict, kind: str) -> None:
    user_id = user["user_id"]
    to_email = user["email"]

    # Link to the read-only account page (a GET that's safe for email scanners
    # to prefetch). The actual pause/resume is a POST the user triggers from a
    # button there, so a link prefetch can never change account state.
    account_url = _account_url(user_id)

    if kind == "pause":
        subject = "Heading into summer? Pause SchoolSkim"
        body_html = _pause_email_html(account_url)
    else:
        subject = "School's starting — resume SchoolSkim?"
        body_html = _resume_email_html(account_url)

    html_body = _email_shell(
        subject, body_html, account_url, _unsubscribe_url(user_id)
    )
    _send_html_email(to_email, subject, html_body, user_id)


def _send_html_email(to_email: str, subject: str, html_body: str, user_id: str):
    unsub_url = _unsubscribe_url(user_id)
    ses.send_raw_email(
        Source=FROM_EMAIL,
        Destinations=[to_email],
        RawMessage={
            "Data": _build_raw_email(
                FROM_EMAIL, to_email, subject, html_body, unsub_url
            )
        },
    )


def _build_raw_email(
    from_email: str, to_email: str, subject: str, html_body: str, unsub_url: str
) -> str:
    from email.mime.text import MIMEText

    msg = MIMEText(html_body, "html", "utf-8")
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["List-Unsubscribe"] = f"<{unsub_url}>"
    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    return msg.as_string()


# ── Tokens / links (mirror digest_cron + web/src/lib/tokens.ts) ──


def _self_service_token(user_id: str) -> str:
    return hmac.new(
        UNSUBSCRIBE_SECRET.encode(),
        f"account:{user_id}".encode(),
        hashlib.sha256,
    ).hexdigest()


def _unsubscribe_token(user_id: str) -> str:
    return hmac.new(
        UNSUBSCRIBE_SECRET.encode(), user_id.encode(), hashlib.sha256
    ).hexdigest()[:16]


def _account_url(user_id: str) -> str:
    return f"{BASE_URL}/account?uid={user_id}&token={_self_service_token(user_id)}"


def _unsubscribe_url(user_id: str) -> str:
    return f"{BASE_URL}/api/unsubscribe?uid={user_id}&token={_unsubscribe_token(user_id)}"


# ── HTML templates ──


def _button(label: str, url: str, color: str) -> str:
    return (
        '<table role="presentation" cellspacing="0" cellpadding="0" '
        'style="margin:20px auto;"><tr>'
        f'<td style="border-radius:8px;background:{color};">'
        f'<a href="{url}" style="display:inline-block;padding:12px 30px;'
        'color:#ffffff;font-size:15px;font-weight:600;text-decoration:none;">'
        f"{label}</a></td></tr></table>"
    )


def _email_shell(
    title: str, body_html: str, account_url: str, unsub_url: str
) -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,
             'Segoe UI',Roboto,sans-serif;">
<div style="max-width:640px;margin:0 auto;padding:20px;">

    <div style="background:#1a73e8;color:#fff;border-radius:12px 12px 0 0;padding:20px 24px;">
        <h1 style="margin:0;font-size:21px;">{title}</h1>
    </div>

    <div style="background:#fff;border-radius:0 0 12px 12px;padding:24px;
                border:1px solid #e0e0e0;border-top:none;">
        {body_html}

        <div style="text-align:center;font-size:12px;color:#aaa;margin-top:24px;
                    padding-top:16px;border-top:1px solid #eee;">
            <p style="margin:6px 0;">
                <a href="{account_url}"
                   style="color:#aaa;text-decoration:underline;">Manage your account</a>
                &middot;
                <a href="{unsub_url}"
                   style="color:#aaa;text-decoration:underline;">Unsubscribe</a>
            </p>
            <p style="margin:8px 0;font-size:11px;color:#bbb;">{COMPANY_ADDRESS}</p>
        </div>
    </div>

</div>
</body>
</html>"""


def _pause_email_html(action_url: str) -> str:
    return (
        '<p style="margin:12px 0;font-size:15px;color:#333;line-height:1.6;">'
        "Summer break is almost here. Since schools go quiet over the summer, "
        "you can <strong>pause SchoolSkim</strong> — we'll stop processing your "
        "forwarded emails and stop billing until you resume. Nothing is "
        "cancelled, and your settings stay exactly as they are."
        "</p>"
        + _button("Pause for the summer", action_url, "#f0ad4e")
        + '<p style="margin:16px 0;font-size:13px;color:#8a6d3b;background:#fcf8e3;'
        'border:1px solid #faebcc;border-radius:8px;padding:12px 14px;'
        'line-height:1.5;">'
        "<strong>One thing to check:</strong> while paused we discard forwarded "
        "emails — we don't store them. Make sure your Gmail/Outlook forwarding "
        "rule keeps a copy in your own inbox so you can still read anything the "
        "school sends over the summer."
        "</p>"
        '<p style="margin:12px 0;font-size:13px;color:#888;line-height:1.6;">'
        "Prefer to keep getting digests through the summer? Just ignore this "
        "email — nothing changes."
        "</p>"
    )


def _resume_email_html(action_url: str) -> str:
    return (
        '<p style="margin:12px 0;font-size:15px;color:#333;line-height:1.6;">'
        "School is starting back up. You paused SchoolSkim for the summer — "
        "resume to start getting your daily digest again. Billing resumes at "
        "the same $3/month."
        "</p>"
        + _button("Resume my digests", action_url, "#1a73e8")
        + '<p style="margin:16px 0;font-size:13px;color:#8a6d3b;background:#fcf8e3;'
        'border:1px solid #faebcc;border-radius:8px;padding:12px 14px;'
        'line-height:1.5;">'
        "<strong>While you stay paused</strong>, forwarded school emails aren't "
        "processed — so keep an eye on your own inbox for anything important "
        "until you resume."
        "</p>"
        '<p style="margin:12px 0;font-size:13px;color:#888;line-height:1.6;">'
        "Not back yet? No problem — stay paused and you won't be charged."
        "</p>"
    )
