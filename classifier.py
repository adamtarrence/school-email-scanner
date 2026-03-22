"""
Importance classifier — sends school emails to Claude for structured classification.

Uses a strict prompt that classifies by importance level to help parents
prioritize what to discuss with their family each evening.
"""

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import date

import anthropic

from config import Config
from gmail_client import EmailMessage


@dataclass
class EmailClassification:
    """Structured classification returned by Claude."""
    message_id: str
    subject: str
    sender: str
    date: str
    summary: str
    action_items: list[str] = field(default_factory=list)
    important_dates: list[str] = field(default_factory=list)
    importance: str = "normal"  # high | normal | low
    child: str = "all"          # child name or "all"
    rfc822_message_id: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _build_system_prompt() -> str:
    """Build a strict classification prompt."""
    children = Config.get_children()
    today = date.today().strftime("%B %d, %Y")

    children_block = ""
    if children:
        child_lines = [f"  - {c['name']} ({c['grade']}, {c['school']})" for c in children]
        children_list = "\n".join(child_lines)
        valid_names = ", ".join(f'"{c["name"]}"' for c in children) + ', or "all"'
        children_block = f"""
This family has the following children:
{children_list}

Classify which child this email pertains to:
- "Mason High" / "MHS" / "10th grade" → Beckett
- "Mason Intermediate" / "MIS" / "6th grade" → Spencer
- District-wide or can't determine → "all"

Set "child" to one of: {valid_names}
"""

    return f"""\
You are classifying school emails for a busy parent. Today is {today}.

Your job: determine how important this email is so the parent knows what to
discuss with their family at dinner tonight.
{children_block}
Return a JSON object:

{{
  "summary": "1-2 sentence summary of the key info.",
  "action_items": ["Specific things the parent needs to do, if any."],
  "important_dates": ["Event or deadline — Date"],
  "importance": "high | normal | low",
  "child": "child name or all"
}}

═══ IMPORTANCE RULES (follow strictly) ═══

HIGH — Requires parent action or awareness this week:
  ✓ School closures, weather delays, early dismissals
  ✓ Safety alerts or emergency communications
  ✓ Forms to sign, fees to pay, or deadlines requiring parent action
  ✓ A teacher/counselor directly flagging a problem or requesting contact
  ✓ Schedule changes (testing days, early release, field trips needing permission)
  ✓ Parent-teacher conference sign-ups or scheduling

NORMAL — Worth knowing but no immediate action needed:
  ✓ Upcoming school events (plays, concerts, spirit weeks)
  ✓ Volunteer opportunities
  ✓ Curriculum or classroom updates from teachers
  ✓ Club or sport announcements
  ✓ General school news and reminders

LOW — Informational only, no discussion needed:
  ✓ Newsletters and general FYI blasts
  ✓ Fundraising, spirit wear, community flyers
  ✓ PTO social events and community promotions
  ✓ Summer camp and extracurricular promotions
  ✓ Automated system notifications (grade posted, absence logged)

═══ KEY PRINCIPLE ═══

The parent will review this digest over dinner with their family. Classify
based on whether they need to take action (HIGH), would want to know about
it (NORMAL), or can safely skip it (LOW). When in doubt, classify as NORMAL.

Return ONLY the JSON object, no markdown fences or extra text.
"""


class Classifier:
    """Classifies school emails using Claude with importance-based rules."""

    def __init__(self):
        if not Config.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is not configured.")
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    def classify(self, email: EmailMessage) -> EmailClassification:
        """Classify a single email's importance and extract key info."""
        body = email.body_text[:6000] if email.body_text else email.snippet

        user_message = (
            f"Subject: {email.subject}\n"
            f"From: {email.sender}\n"
            f"Date: {email.date}\n\n"
            f"{body}"
        )

        if len(user_message) > 15000:
            user_message = user_message[:15000] + "\n\n[Truncated]"

        response = self.client.messages.create(
            model=Config.ANTHROPIC_MODEL,
            max_tokens=512,
            system=_build_system_prompt(),
            messages=[{"role": "user", "content": user_message}],
        )

        raw_text = response.content[0].text.strip()

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if match:
                data = json.loads(match.group())
            else:
                data = {
                    "summary": raw_text[:500],
                    "action_items": [],
                    "important_dates": [],
                    "importance": "normal",
                    "child": "all",
                }

        # Validate child field
        child_value = data.get("child", "all")
        children = Config.get_children()
        valid_names = [c["name"].lower() for c in children] + ["all"]
        if child_value.lower() not in valid_names:
            child_value = "all"
        for c in children:
            if child_value.lower() == c["name"].lower():
                child_value = c["name"]
                break

        return EmailClassification(
            message_id=email.message_id,
            subject=email.subject,
            sender=email.sender,
            date=email.date,
            summary=data.get("summary", ""),
            action_items=data.get("action_items", []),
            important_dates=data.get("important_dates", []),
            importance=data.get("importance", "normal"),
            child=child_value,
            rfc822_message_id=email.rfc822_message_id,
        )

    def classify_batch(self, emails: list[EmailMessage]) -> list[EmailClassification]:
        """Classify a list of emails, skipping auto-skip senders."""
        results = []
        for email in emails:
            if Config.should_auto_skip(email.sender, email.subject):
                results.append(EmailClassification(
                    message_id=email.message_id,
                    subject=email.subject,
                    sender=email.sender,
                    date=email.date,
                    summary=f"Auto-skipped: {email.snippet[:100]}",
                    importance="low",
                    child="all",
                    rfc822_message_id=email.rfc822_message_id,
                ))
                print(f"  ⏭  Auto-skipped: {email.subject[:60]}")
                continue

            try:
                print(f"  → Classifying: {email.subject[:60]}")
                result = self.classify(email)
                results.append(result)
                icon = {"high": "🔴", "normal": "🟡", "low": "⚪"}.get(result.importance, "🟡")
                print(f"  {icon} {result.importance.upper()}: {email.subject[:60]}")
            except Exception as e:
                print(f"  ✗ Failed: {email.subject[:60]} — {e}")

        return results
