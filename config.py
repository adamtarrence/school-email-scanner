"""Configuration loader for school email scanner."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the same directory as this file (local dev only; CI uses env vars)
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


class Config:
    """Central configuration loaded from environment variables."""

    # Anthropic
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    # Email
    EMAIL_TO = os.getenv("EMAIL_TO", "")

    # Children: "Name:Grade:School;Name2:Grade2:School2"
    CHILDREN_RAW = os.getenv("CHILDREN", "")

    # Gmail
    SCHOOL_DOMAINS = [
        d.strip()
        for d in os.getenv("SCHOOL_DOMAINS", "").split(",")
        if d.strip()
    ]

    # ── Auto-skip rules ──
    # Emails matching these rules are never sent to Claude for classification.
    # They're automatically treated as LOW importance.
    AUTO_SKIP_SENDERS = [
        "school@peachjar.com",          # Community flyers
        "no-reply@schoology.com",       # Grade summaries, course updates
    ]
    AUTO_SKIP_SENDER_DOMAINS = [
        "masonohioschoolscom.myenotice.com",  # District newsletters (eNotice)
    ]
    AUTO_SKIP_SUBJECT_PATTERNS = [
        "Student Absence Received",     # SafeArrival confirmations
        "Weekly Schoology Summary",     # Weekly grade reports
    ]

    # ── Digest exclusions ──
    # Prevent the digest from including its own past output
    DIGEST_EXCLUDE_SENDERS = [
        "adam.tarrence@gmail.com",
        "sarah.tarrence@gmail.com",
    ]
    DIGEST_EXCLUDE_SUBJECTS = [
        "Daily School Digest",
        "Weekly School Recap",
    ]

    @classmethod
    def get_children(cls) -> list[dict]:
        """Parse CHILDREN env var into structured list."""
        if not cls.CHILDREN_RAW:
            return []
        children = []
        for entry in cls.CHILDREN_RAW.split(";"):
            parts = entry.strip().split(":")
            if len(parts) == 3:
                children.append({
                    "name": parts[0].strip(),
                    "grade": parts[1].strip(),
                    "school": parts[2].strip(),
                })
        return children

    @classmethod
    def gmail_query(cls, hours_back: int = 0) -> str:
        """Build a Gmail search query for school emails."""
        import time

        domain_clauses = [f"from:@{d}" for d in cls.SCHOOL_DOMAINS]
        query = f"({' OR '.join(domain_clauses)})"

        if hours_back:
            cutoff = int(time.time()) - (hours_back * 3600)
            query += f" after:{cutoff}"

        return query

    @classmethod
    def digest_query(cls, hours_back: int = 28) -> str:
        """Build a Gmail query for the digest, with exclusions."""
        base = cls.gmail_query(hours_back=hours_back)

        # Exclude our own emails and past digests
        for sender in cls.DIGEST_EXCLUDE_SENDERS:
            base += f" -from:{sender}"
        for subject in cls.DIGEST_EXCLUDE_SUBJECTS:
            base += f' -subject:"{subject}"'

        return base

    @classmethod
    def should_auto_skip(cls, sender: str, subject: str) -> bool:
        """Check if an email should be auto-skipped (never sent to Claude)."""
        sender_lower = sender.lower()

        for skip_sender in cls.AUTO_SKIP_SENDERS:
            if skip_sender.lower() in sender_lower:
                return True

        for skip_domain in cls.AUTO_SKIP_SENDER_DOMAINS:
            if skip_domain.lower() in sender_lower:
                return True

        subject_lower = subject.lower()
        for pattern in cls.AUTO_SKIP_SUBJECT_PATTERNS:
            if pattern.lower() in subject_lower:
                return True

        return False
