#!/usr/bin/env python3
"""
School Email Digest — daily evening summary + compact weekly recap.

Daily mode:  Full card-based digest of today's school emails, grouped by child.
Weekly mode: Compact list of HIGH/NORMAL items from the past week.

Usage:
    python3 digest.py                          # Daily digest (default)
    python3 digest.py --mode weekly             # Weekly recap
    python3 digest.py --dry-run                 # Preview HTML without sending
    python3 digest.py --mode weekly --dry-run   # Preview weekly recap
"""

import argparse
import sys
from datetime import datetime, timedelta
from urllib.parse import quote

from config import Config
from gmail_client import GmailClient
from classifier import Classifier, EmailClassification


# ── Link helpers ──

def _mail_app_url(rfc822_message_id: str) -> str:
    """Build a message:// URL that opens in Apple Mail."""
    mid = rfc822_message_id.strip("<>")
    return f"message://%3C{quote(mid, safe='@.')}%3E"


def _gmail_url(message_id: str) -> str:
    """Gmail web link fallback."""
    return f"https://mail.google.com/mail/u/0/#all/{message_id}"


def _email_link(classification: EmailClassification) -> str:
    """Get the best link for an email — Apple Mail preferred."""
    if classification.rfc822_message_id:
        return _mail_app_url(classification.rfc822_message_id)
    return _gmail_url(classification.message_id)


# ── Grouping helper ──

def _group_by_child(classifications: list[EmailClassification]) -> dict[str, list[EmailClassification]]:
    """Group classifications by child, with importance sorting."""
    children = Config.get_children()
    child_names = [c["name"] for c in children]

    groups: dict[str, list[EmailClassification]] = {}
    for name in child_names:
        groups[name] = []
    groups["District / Other"] = []

    for c in classifications:
        if c.child in child_names:
            groups[c.child].append(c)
        else:
            groups["District / Other"].append(c)

    importance_order = {"high": 0, "normal": 1, "low": 2}
    for group in groups.values():
        group.sort(key=lambda x: importance_order.get(x.importance, 1))

    return groups


# ── HTML builders ──

def _importance_badge(importance: str) -> str:
    """Colored badge HTML for importance level."""
    colors = {
        "high": ("#dc3545", "#fff"),
        "normal": ("#6c757d", "#fff"),
        "low": ("#adb5bd", "#333"),
    }
    bg, fg = colors.get(importance, colors["normal"])
    return (
        f'<span style="display:inline-block;padding:2px 8px;border-radius:10px;'
        f'font-size:11px;font-weight:600;background:{bg};color:{fg};'
        f'text-transform:uppercase;">{importance}</span>'
    )


def build_daily_html(classifications: list[EmailClassification]) -> str:
    """Build a responsive HTML daily digest email grouped by child."""
    children = Config.get_children()
    child_info = {c["name"]: f"{c['grade']}, {c['school']}" for c in children}
    now = datetime.now()
    groups = _group_by_child(classifications)

    sections_html = ""
    total_count = 0

    for group_name, items in groups.items():
        if not items:
            continue

        total_count += len(items)
        subtitle = child_info.get(group_name, "District-wide communications")

        cards_html = ""
        for item in items:
            link = _email_link(item)
            badge = _importance_badge(item.importance)

            action_html = ""
            if item.action_items:
                action_items = "".join(
                    f"<li style='margin-bottom:4px;'>{a}</li>"
                    for a in item.action_items
                )
                action_html = (
                    f'<div style="margin-top:10px;padding:8px 12px;'
                    f'background:#fff3cd;border-radius:6px;border-left:3px solid #ffc107;">'
                    f'<strong style="font-size:12px;color:#856404;">⚡ ACTION NEEDED</strong>'
                    f'<ul style="margin:4px 0 0 0;padding-left:18px;font-size:13px;">'
                    f'{action_items}</ul></div>'
                )

            dates_html = ""
            if item.important_dates:
                date_items = "".join(
                    f"<li style='margin-bottom:2px;'>{d}</li>"
                    for d in item.important_dates
                )
                dates_html = (
                    f'<div style="margin-top:8px;padding:8px 12px;'
                    f'background:#e8f4fd;border-radius:6px;border-left:3px solid #0d6efd;">'
                    f'<strong style="font-size:12px;color:#084298;">📅 KEY DATES</strong>'
                    f'<ul style="margin:4px 0 0 0;padding-left:18px;font-size:13px;">'
                    f'{date_items}</ul></div>'
                )

            sender_display = item.sender.split("<")[0].strip().strip('"')
            if not sender_display:
                sender_display = item.sender

            cards_html += f"""
            <div style="background:#fff;border:1px solid #e0e0e0;border-radius:8px;
                        padding:16px;margin-bottom:12px;">
                <div style="display:flex;justify-content:space-between;align-items:center;
                            margin-bottom:8px;">
                    <a href="{link}" style="color:#1a73e8;text-decoration:none;
                       font-weight:600;font-size:15px;flex:1;">
                        {item.subject}
                    </a>
                    {badge}
                </div>
                <div style="font-size:12px;color:#666;margin-bottom:8px;">
                    From: {sender_display} &middot; {item.date[:16] if len(item.date) > 16 else item.date}
                </div>
                <div style="font-size:14px;color:#333;line-height:1.5;">
                    {item.summary}
                </div>
                {action_html}
                {dates_html}
            </div>
            """

        sections_html += f"""
        <div style="margin-bottom:24px;">
            <h2 style="margin:0 0 4px 0;font-size:20px;color:#1a1a1a;">
                {group_name}
            </h2>
            <div style="font-size:13px;color:#888;margin-bottom:12px;">
                {subtitle} &middot; {len(items)} email(s)
            </div>
            {cards_html}
        </div>
        """

    total_actions = sum(len(c.action_items) for c in classifications)
    action_banner = ""
    if total_actions > 0:
        action_banner = (
            f'<div style="background:#fff3cd;border:1px solid #ffc107;border-radius:8px;'
            f'padding:12px 16px;margin-bottom:20px;font-size:14px;color:#856404;">'
            f'⚡ <strong>{total_actions} action item(s)</strong> need your attention.'
            f'</div>'
        )

    no_emails_msg = ""
    if total_count == 0:
        no_emails_msg = (
            '<div style="text-align:center;padding:30px 0;color:#888;font-size:15px;">'
            'No school emails today. Enjoy the quiet evening!'
            '</div>'
        )

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,
             'Segoe UI',Roboto,sans-serif;">
<div style="max-width:640px;margin:0 auto;padding:20px;">

    <div style="background:#1a73e8;color:#fff;border-radius:12px 12px 0 0;padding:20px 24px;">
        <h1 style="margin:0;font-size:22px;">📚 Daily School Digest</h1>
        <div style="font-size:13px;opacity:0.85;margin-top:4px;">
            {now.strftime('%A, %B %d, %Y')} &middot; {total_count} email(s)
        </div>
    </div>

    <div style="background:#fff;border-radius:0 0 12px 12px;padding:20px 24px;
                border:1px solid #e0e0e0;border-top:none;">
        {action_banner}
        {sections_html}
        {no_emails_msg}

        <div style="text-align:center;font-size:12px;color:#aaa;margin-top:20px;
                    padding-top:16px;border-top:1px solid #eee;">
            Generated by School Email Scanner<br>
            Links open in Apple Mail
        </div>
    </div>

</div>
</body>
</html>"""

    return html


def build_weekly_html(classifications: list[EmailClassification]) -> str:
    """Build a compact weekly recap — HIGH and NORMAL items only."""
    children = Config.get_children()
    child_info = {c["name"]: f"{c['grade']}, {c['school']}" for c in children}
    now = datetime.now()
    week_start = (now - timedelta(days=7)).strftime("%b %d")
    week_end = now.strftime("%b %d, %Y")

    # Filter to HIGH and NORMAL only
    filtered = [c for c in classifications if c.importance in ("high", "normal")]
    groups = _group_by_child(filtered)

    sections_html = ""
    total_count = 0

    for group_name, items in groups.items():
        if not items:
            continue

        total_count += len(items)
        subtitle = child_info.get(group_name, "District-wide")

        rows_html = ""
        for item in items:
            link = _email_link(item)

            # Compact: importance dot + linked subject + action note
            dot_color = "#dc3545" if item.importance == "high" else "#6c757d"
            action_note = ""
            if item.action_items:
                action_note = (
                    f'<span style="color:#856404;font-size:12px;"> — '
                    f'{item.action_items[0]}</span>'
                )

            rows_html += f"""
            <div style="padding:6px 0;border-bottom:1px solid #f0f0f0;">
                <span style="display:inline-block;width:8px;height:8px;border-radius:50%;
                             background:{dot_color};margin-right:8px;vertical-align:middle;"></span>
                <a href="{link}" style="color:#1a73e8;text-decoration:none;font-size:14px;">
                    {item.subject}
                </a>
                {action_note}
            </div>
            """

        sections_html += f"""
        <div style="margin-bottom:20px;">
            <h2 style="margin:0 0 8px 0;font-size:17px;color:#1a1a1a;">
                {group_name}
            </h2>
            <div style="font-size:12px;color:#888;margin-bottom:8px;">
                {subtitle} &middot; {len(items)} item(s)
            </div>
            {rows_html}
        </div>
        """

    no_items_msg = ""
    if total_count == 0:
        no_items_msg = (
            '<div style="text-align:center;padding:20px 0;color:#888;font-size:14px;">'
            'Nothing notable this week!'
            '</div>'
        )

    # Collect all action items across the week
    all_actions = []
    for c in filtered:
        for a in c.action_items:
            all_actions.append((c.child, a))

    action_summary = ""
    if all_actions:
        action_lines = "".join(
            f"<li style='margin-bottom:4px;'><strong>{child}:</strong> {action}</li>"
            if child != "all" else f"<li style='margin-bottom:4px;'>{action}</li>"
            for child, action in all_actions
        )
        action_summary = (
            f'<div style="background:#fff3cd;border:1px solid #ffc107;border-radius:8px;'
            f'padding:12px 16px;margin-bottom:20px;font-size:13px;color:#856404;">'
            f'<strong>⚡ Open Action Items</strong>'
            f'<ul style="margin:8px 0 0 0;padding-left:18px;">{action_lines}</ul>'
            f'</div>'
        )

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,
             'Segoe UI',Roboto,sans-serif;">
<div style="max-width:640px;margin:0 auto;padding:20px;">

    <div style="background:#2d5016;color:#fff;border-radius:12px 12px 0 0;padding:16px 24px;">
        <h1 style="margin:0;font-size:20px;">📋 Weekly School Recap</h1>
        <div style="font-size:13px;opacity:0.85;margin-top:4px;">
            {week_start} – {week_end} &middot; {total_count} notable item(s)
        </div>
    </div>

    <div style="background:#fff;border-radius:0 0 12px 12px;padding:16px 24px;
                border:1px solid #e0e0e0;border-top:none;">
        {action_summary}
        {sections_html}
        {no_items_msg}

        <div style="text-align:center;font-size:12px;color:#aaa;margin-top:16px;
                    padding-top:12px;border-top:1px solid #eee;">
            Generated by School Email Scanner<br>
            Links open in Apple Mail
        </div>
    </div>

</div>
</body>
</html>"""

    return html


# ── Main logic ──

def run_digest(mode: str = "daily", dry_run: bool = False):
    """Generate and optionally send a digest email."""
    is_weekly = mode == "weekly"
    hours_back = 168 if is_weekly else 28
    label = "Weekly School Recap" if is_weekly else "Daily School Digest"

    print(f"📚 {label}\n")
    print(f"   Looking back {hours_back} hours...")

    if not Config.ANTHROPIC_API_KEY:
        print("✗ ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    # 1. Fetch school emails
    print("📧 Connecting to Gmail...")
    gmail = GmailClient()
    gmail.authenticate()

    query = Config.digest_query(hours_back=hours_back)
    print(f"🔍 Query: {query[:100]}...")
    emails = gmail.fetch_emails(query, max_results=100)
    print(f"   Found {len(emails)} email(s).")

    if not emails:
        if not is_weekly:
            print("✅ No school emails today. Nothing to digest!")
        else:
            print("✅ No school emails this week.")
        return

    # 2. Classify all emails
    print(f"\n🤖 Classifying {len(emails)} email(s)...")
    classifier = Classifier()
    classifications = classifier.classify_batch(emails)

    if not classifications:
        print("⚠ No classifications generated.")
        return

    # 3. Build HTML
    print(f"\n📝 Building {mode} HTML...")
    if is_weekly:
        html = build_weekly_html(classifications)
    else:
        html = build_daily_html(classifications)

    if dry_run:
        from pathlib import Path
        preview_path = Path(__file__).parent / "digest_preview.html"
        preview_path.write_text(html)
        print(f"\n✅ Dry run — preview saved to: {preview_path}")
        print(f"   Open it in a browser to see the {mode} digest.")

        print(f"\n   Summary: {len(classifications)} emails classified:")
        for c in classifications:
            icon = {"high": "🔴", "normal": "🟡", "low": "⚪"}.get(c.importance, "🟡")
            child_tag = f" [{c.child}]" if c.child != "all" else ""
            print(f"     {icon} {c.subject[:60]}{child_tag}")
        return

    # 4. Send digest email
    if not Config.EMAIL_TO:
        print("✗ EMAIL_TO not set.")
        sys.exit(1)

    now = datetime.now()
    if is_weekly:
        week_start = (now - timedelta(days=7)).strftime("%b %d")
        subject = f"Weekly School Recap — {week_start}–{now.strftime('%b %d, %Y')}"
    else:
        subject = f"Daily School Digest — {now.strftime('%b %d, %Y')}"

    print(f"\n📤 Sending to {Config.EMAIL_TO}...")
    gmail.send_html_email(Config.EMAIL_TO, subject, html)
    print(f"✅ {label} sent!")


def main():
    parser = argparse.ArgumentParser(description="School email digest generator.")
    parser.add_argument("--mode", choices=["daily", "weekly"], default="daily",
                        help="Digest mode: daily (default) or weekly recap.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview digest without sending email.")
    args = parser.parse_args()

    run_digest(mode=args.mode, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
