"""
Lambda handler: Daily digest cron.

Triggered by EventBridge every hour (22-03 UTC, covering US evening times).
For each user whose digest time falls in the current hour, pulls the last
24h of stored emails, summarizes via Claude, and sends the digest via SES.
"""

import hashlib
import hmac
import html
import os
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
from zoneinfo import ZoneInfo

import anthropic
import boto3
from boto3.dynamodb.conditions import Attr, Key

dynamodb = boto3.resource("dynamodb")
ses = boto3.client("ses")

USERS_TABLE = os.environ["USERS_TABLE"]
EMAILS_TABLE = os.environ["EMAILS_TABLE"]
DIGESTS_TABLE = os.environ["DIGESTS_TABLE"]
FROM_EMAIL = os.environ.get("FROM_EMAIL", "digest@schoolskim.com")
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
UNSUBSCRIBE_SECRET = os.environ.get("UNSUBSCRIBE_SECRET", "schoolskim-unsub-default")
COMPANY_ADDRESS = "SchoolSkim, 10685-B Hazelhurst Dr. #42818, Houston, TX 77043"


def lambda_handler(event, context):
    """Find users due for a digest this hour and send them."""
    now_utc = datetime.now(timezone.utc)
    users = _get_users_due_now(now_utc)

    print(f"Found {len(users)} user(s) due for digest at {now_utc.isoformat()}")

    for user in users:
        try:
            _process_user_digest(user, now_utc)
        except Exception as e:
            print(f"Error processing digest for {user['user_id']}: {e}")

    return {"processed": len(users)}


def _get_users_due_now(now_utc: datetime) -> list[dict]:
    """Scan Users table for users whose digest hour matches the current UTC hour."""
    table = dynamodb.Table(USERS_TABLE)
    resp = table.scan(FilterExpression=Attr("status").ne("inactive"))
    users = resp.get("Items", [])

    due = []
    for user in users:
        tz_name = user.get("timezone", "America/New_York")
        digest_time = user.get("digest_time", "18:00")
        digest_hour = int(digest_time.split(":")[0])

        # Convert user's desired local hour to UTC and check if it matches now
        utc_hour = _local_hour_to_utc(digest_hour, tz_name)
        if utc_hour == now_utc.hour:
            due.append(user)

    return due


def _local_hour_to_utc(local_hour: int, tz_name: str) -> int:
    """Convert a local hour to UTC hour using real timezone data (handles DST)."""
    now_utc = datetime.now(timezone.utc)
    try:
        tz = ZoneInfo(tz_name)
    except KeyError:
        tz = ZoneInfo("America/New_York")
    offset_seconds = now_utc.astimezone(tz).utcoffset().total_seconds()
    offset_hours = offset_seconds / 3600
    return int((local_hour - offset_hours) % 24)


def _process_user_digest(user: dict, now_utc: datetime):
    """Build and send a digest for one user."""
    user_id = user["user_id"]
    user_email = user["email"]
    children = user.get("children", [])

    # Fetch emails from the last 28 hours
    cutoff = (now_utc - timedelta(hours=28)).isoformat()
    emails = _fetch_user_emails(user_id, cutoff)

    date_str = now_utc.strftime("%A, %B %d, %Y")

    if not emails:
        print(f"No emails for {user_id}, sending quiet day digest.")
        digest_md = "Quiet day \u2014 nothing from the schools today."
    else:
        print(f"Summarizing {len(emails)} email(s) for {user_id}...")
        digest_md = _summarize(emails, children)

    # Build HTML
    html_body = _build_html(digest_md, date_str, user_email, user_id)

    # Send via SES
    subject = f"Daily School Digest \u2014 {now_utc.strftime('%b %d, %Y')}"
    _send_email(user_email, subject, html_body, user_id)

    # Store digest record
    _store_digest(user_id, now_utc.isoformat(), digest_md, len(emails))

    print(f"Digest sent to {user_email}")


def _fetch_user_emails(user_id: str, since_iso: str) -> list[dict]:
    """Get stored emails for a user since the cutoff time."""
    table = dynamodb.Table(EMAILS_TABLE)
    resp = table.query(
        KeyConditionExpression=(
            Key("user_id").eq(user_id) & Key("received_at").gte(since_iso)
        )
    )
    return resp.get("Items", [])


# ── Summarization (ported from summarizer.py) ──


def _build_system_prompt(children: list[dict]) -> str:
    today = datetime.now(timezone.utc).strftime("%A, %B %d, %Y")

    if children:
        child_lines = "\n".join(
            f"  - {c['name']} ({c.get('grade', '')},"
            f" {c.get('school', '')})"
            for c in children
        )
    else:
        child_lines = "  - (no children configured)"

    return f"""\
You are a parent's email assistant. Your job is to read all of today's school
emails and write a brief daily digest that a busy parent can scan in under
2 minutes over dinner.

Today is {today}.

This family has the following children:
{child_lines}

RULES:
1. Lead with ACTION ITEMS — things the parent must do (sign forms, pay fees,
   reply to a teacher, meet a deadline). Bold the action and include the
   deadline if there is one.
2. Then list UPCOMING EVENTS worth knowing about (concerts, spirit weeks,
   schedule changes, early dismissals).
3. Include a QUICK HITS section for low-priority but mildly interesting items
   (club meetings, classroom updates, etc.) — just a few words each.
4. SKIP entirely: fundraising, spirit wear, community flyers, automated
   notifications (absence logged).
5. Use markdown: headers (##), bold, bullets. Keep it concise.
6. Do NOT write long summaries. A few words per item is ideal.
7. Classify which child each item pertains to based on the school name or
   grade level mentioned in the email. If unclear, mark as "General".

Omit any section that has no items (but always include at least Quick Hits
if there are any emails at all)."""


def _format_email_for_prompt(index: int, em: dict) -> str:
    body = (em.get("body", "") or "")[:4000]
    return (
        f"--- EMAIL-{index} ---\n"
        f"Subject: {em.get('subject', '(no subject)')}\n"
        f"From: {em.get('sender', 'unknown')}\n"
        f"Date: {em.get('received_at', '')}\n\n"
        f"{body}"
    )


def _summarize(emails: list[dict], children: list[dict]) -> str:
    """Send all emails to Claude in one batch and get a digest."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    email_blocks = [
        _format_email_for_prompt(i, em) for i, em in enumerate(emails, 1)
    ]
    user_message = "\n\n".join(email_blocks)

    if len(user_message) > 80000:
        user_message = user_message[:80000] + "\n\n[Remaining emails truncated]"

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2048,
        system=_build_system_prompt(children),
        messages=[{"role": "user", "content": user_message}],
    )

    return response.content[0].text.strip()


# ── HTML rendering (ported from digest.py) ──


def _inline_markdown(text: str) -> str:
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    parts = []
    last_end = 0
    for match in link_pattern.finditer(text):
        parts.append(html.escape(text[last_end : match.start()]))
        link_text = html.escape(match.group(1))
        url = match.group(2)
        parts.append(
            f'<a href="{url}" style="color:#1a73e8;text-decoration:none;">'
            f"{link_text}</a>"
        )
        last_end = match.end()
    parts.append(html.escape(text[last_end:]))
    result = "".join(parts)
    result = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", result)
    return result


def _markdown_to_html(md: str) -> str:
    lines = md.split("\n")
    html_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()

        if in_list and not stripped.startswith("- "):
            html_lines.append("</ul>")
            in_list = False

        if not stripped:
            html_lines.append("<br>")
            continue

        if stripped.startswith("## "):
            text = html.escape(stripped[3:])
            html_lines.append(
                f'<h2 style="margin:18px 0 8px 0;font-size:17px;color:#1a1a1a;'
                f'border-bottom:1px solid #eee;padding-bottom:4px;">{text}</h2>'
            )
            continue

        if stripped.startswith("- "):
            if not in_list:
                html_lines.append(
                    '<ul style="margin:4px 0;padding-left:20px;font-size:14px;'
                    'line-height:1.7;color:#333;">'
                )
                in_list = True
            item_html = _inline_markdown(stripped[2:])
            html_lines.append(f"<li style='margin-bottom:4px;'>{item_html}</li>")
            continue

        text = _inline_markdown(stripped)
        html_lines.append(
            f'<p style="margin:6px 0;font-size:14px;color:#333;'
            f'line-height:1.6;">{text}</p>'
        )

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


def _unsubscribe_token(user_id: str) -> str:
    """Generate HMAC token for unsubscribe links."""
    return hmac.new(
        UNSUBSCRIBE_SECRET.encode(), user_id.encode(), hashlib.sha256
    ).hexdigest()[:16]


def _unsubscribe_url(user_id: str) -> str:
    token = _unsubscribe_token(user_id)
    return f"https://schoolskim.com/api/unsubscribe?uid={user_id}&token={token}"


def _feedback_mailto(date_str: str, user_email: str) -> str:
    subject = quote(f"[SchoolSkim Feedback] Digest for {date_str}")
    body = quote(
        "What was missing or wrong in today's digest?\n\n"
        "[ ] Something important was left out\n"
        "[ ] Something unimportant was included\n"
        "[ ] Summary was unclear or inaccurate\n"
        "[ ] Other\n\n"
        "Details:\n"
    )
    return f"mailto:hello@schoolskim.com?subject={subject}&body={body}"


def _build_html(
    digest_md: str, date_str: str, user_email: str, user_id: str
) -> str:
    content_html = _markdown_to_html(digest_md)
    feedback_url = _feedback_mailto(date_str, user_email)
    unsub_url = _unsubscribe_url(user_id)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,
             'Segoe UI',Roboto,sans-serif;">
<div style="max-width:640px;margin:0 auto;padding:20px;">

    <div style="background:#1a73e8;color:#fff;border-radius:12px 12px 0 0;padding:20px 24px;">
        <h1 style="margin:0;font-size:22px;">Daily School Digest</h1>
        <div style="font-size:13px;opacity:0.85;margin-top:4px;">
            {date_str}
        </div>
    </div>

    <div style="background:#fff;border-radius:0 0 12px 12px;padding:20px 24px;
                border:1px solid #e0e0e0;border-top:none;">
        {content_html}

        <div style="text-align:center;font-size:12px;color:#aaa;margin-top:20px;
                    padding-top:16px;border-top:1px solid #eee;">
            <p style="margin:6px 0;">
                Generated by SchoolSkim &middot;
                <a href="{feedback_url}"
                   style="color:#aaa;text-decoration:underline;">Something missing or wrong?</a>
                &middot;
                <a href="{unsub_url}"
                   style="color:#aaa;text-decoration:underline;">Unsubscribe</a>
            </p>
            <p style="margin:8px 0;font-size:11px;color:#bbb;">
                {COMPANY_ADDRESS}
            </p>
        </div>
    </div>

</div>
</body>
</html>"""


# ── Email sending ──


def _send_email(to_email: str, subject: str, html_body: str, user_id: str):
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
    from_email: str,
    to_email: str,
    subject: str,
    html_body: str,
    unsub_url: str,
) -> str:
    """Build a raw MIME email with List-Unsubscribe headers."""
    from email.mime.text import MIMEText

    msg = MIMEText(html_body, "html", "utf-8")
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["List-Unsubscribe"] = f"<{unsub_url}>"
    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    return msg.as_string()


# ── Digest storage ──


def _store_digest(
    user_id: str, sent_at: str, markdown: str, email_count: int
):
    table = dynamodb.Table(DIGESTS_TABLE)
    table.put_item(
        Item={
            "user_id": user_id,
            "sent_at": sent_at,
            "markdown": markdown,
            "email_count": email_count,
        }
    )
