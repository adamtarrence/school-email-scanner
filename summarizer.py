"""
Batch email summarizer — sends all school emails to Claude in one call
and gets back a concise briefing-style digest with clickable links.
"""

from datetime import date
from urllib.parse import quote

import anthropic

from config import Config
from gmail_client import EmailMessage
from url_fetcher import extract_first_url, fetch_linked_content, is_login_required


def _mail_app_url(rfc822_message_id: str) -> str:
    """Build a message:// URL that opens in Apple Mail / Mimestream."""
    mid = rfc822_message_id.strip("<>")
    return f"message://%3C{quote(mid, safe='@.')}%3E"


def _gmail_url(gmail_id: str) -> str:
    """Gmail web link."""
    return f"https://mail.google.com/mail/u/0/#all/{gmail_id}"


def _build_system_prompt() -> str:
    """Build the batch summarization prompt."""
    children = Config.get_children()
    today = date.today().strftime("%A, %B %d, %Y")

    child_lines = "\n".join(
        f"  - {c['name']} ({c['grade']}, {c['school']})" for c in children
    )

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
   (club meetings, classroom updates, etc.) — just a few words each. This
   section keeps the parent in the loop without being overwhelming.
4. SKIP entirely:
   - Fundraising, spirit wear, community flyers
   - Automated notifications (absence logged)
5. Handle LINK-ONLY emails carefully:
   - Some emails are marked with [LINK-ONLY: url] — the email was just a
     notification stub with no real content in the body.
   - If the email also has [FETCHED CONTENT] below it, summarize that
     content as you would any other email.
   - If it only has [LINK-ONLY: url] with no fetched content, include a
     brief line in Quick Hits with a note like "(login required to view)"
     so the parent knows something was posted. Do NOT skip these silently —
     the parent should know something exists even if we can't read it.
6. Use markdown: headers (##), bold, bullets. Keep it concise.
7. Do NOT write long summaries. A few words per item is ideal.

LINKS:
Each email has an ID like [EMAIL-3]. When you mention an item, make the key
phrase a markdown link using that ID. Example:
  - **Spencer**: [Art club meeting moved to Thursday](EMAIL-2)
The link placeholder will be replaced with a real URL after you respond.
Every bullet point should include at least one link so the parent can click
through to read more.

Classify which child each item pertains to:
- "Mason High" / "MHS" / "10th grade" → Beckett
- "Mason Intermediate" / "MIS" / "6th grade" → Spencer
- District-wide or can't determine → both/district

FORMAT your response like this:

## Action Items
- **Beckett**: [Sign field trip permission slip](EMAIL-1) — due Friday
- **Spencer**: [Pay lunch balance](EMAIL-3) — $15

## Coming Up
- **Spencer**: [Science fair](EMAIL-2) — April 5
- **Beckett**: [SAT prep workshop](EMAIL-4) — next Wednesday

## Quick Hits
- **Spencer**: [Art club](EMAIL-5) is doing watercolors this week
- **District**: [Spring break](EMAIL-6) reminder — April 14-18

Omit any section that has no items (but always include at least Quick Hits
if there are any emails at all — there's always something worth a brief
mention)."""


def _format_email(index: int, email: EmailMessage) -> str:
    """Format a single email for inclusion in the batch prompt.

    For notification stub emails (e.g. "Spencer's teacher posted an assignment"),
    we attempt to fetch the linked content. If the content is publicly accessible
    we include it so Claude can summarize it. If it requires login, we annotate
    with [LINK-ONLY] so Claude surfaces it rather than silently dropping it.
    """
    body = email.body_text[:4000] if email.body_text else email.snippet
    header = (
        f"--- EMAIL-{index} ---\n"
        f"Subject: {email.subject}\n"
        f"From: {email.sender}\n"
        f"Date: {email.date}\n\n"
        f"{body}"
    )

    if not Config.is_notification_stub(email.subject):
        return header

    # This looks like a portal notification — try to fetch the linked content
    url = extract_first_url(body or "")
    if not url:
        return header

    if is_login_required(url):
        return header + f"\n\n[LINK-ONLY: {url}]"

    print(f"  🔗 Fetching linked content: {url[:80]}...")
    content, requires_login = fetch_linked_content(url)

    if requires_login:
        return header + f"\n\n[LINK-ONLY: {url}]"

    if content:
        return header + f"\n\n[FETCHED CONTENT from {url}]\n{content}"

    # Fetch failed or returned nothing — still flag it
    return header + f"\n\n[LINK-ONLY: {url}]"


def _replace_email_links(markdown: str, link_map: dict[str, tuple[str, str]]) -> str:
    """Replace EMAIL-N placeholders with real URLs.

    Each link becomes two side-by-side links: one for Apple Mail/Mimestream,
    one for Gmail web.
    """
    import re

    def replacer(match):
        text = match.group(1)
        email_id = match.group(2)
        if email_id in link_map:
            mail_url, gmail_link = link_map[email_id]
            # Primary link goes to Apple Mail/Mimestream; Gmail fallback in parens
            return f'[{text}]({mail_url}) ([web]({gmail_link}))'
        return text

    return re.sub(r'\[([^\]]+)\]\((EMAIL-\d+)\)', replacer, markdown)


class Summarizer:
    """Batch email summarizer using Claude."""

    def __init__(self):
        if not Config.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is not configured.")
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    def summarize(self, emails: list[EmailMessage]) -> str:
        """Send all emails to Claude in one batch and get a briefing-style digest.

        Returns markdown text with clickable links, ready to be wrapped in HTML.
        """
        # Filter out auto-skip emails before sending to Claude
        kept = []
        for email in emails:
            if Config.should_auto_skip(email.sender, email.subject):
                print(f"  ⏭  Auto-skipped: {email.subject[:60]}")
            else:
                kept.append(email)

        if not kept:
            return "Quiet day — nothing from the schools today."

        print(f"  Sending {len(kept)} email(s) to Claude for summarization...")

        # Build link map: EMAIL-N -> (message:// URL, Gmail URL)
        link_map = {}
        for i, email in enumerate(kept, 1):
            key = f"EMAIL-{i}"
            mail_url = _mail_app_url(email.rfc822_message_id) if email.rfc822_message_id else _gmail_url(email.message_id)
            gmail_link = _gmail_url(email.message_id)
            link_map[key] = (mail_url, gmail_link)

        # Build the batch content
        email_blocks = [_format_email(i, email) for i, email in enumerate(kept, 1)]
        user_message = "\n\n".join(email_blocks)

        # Truncate if too long (stay well within context limits)
        if len(user_message) > 80000:
            user_message = user_message[:80000] + "\n\n[Remaining emails truncated]"

        response = self.client.messages.create(
            model=Config.ANTHROPIC_MODEL,
            max_tokens=2048,
            system=_build_system_prompt(),
            messages=[{"role": "user", "content": user_message}],
        )

        markdown = response.content[0].text.strip()

        # Replace EMAIL-N placeholders with real clickable links
        return _replace_email_links(markdown, link_map)
