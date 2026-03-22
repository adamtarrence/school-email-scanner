"""Gmail API client — authentication, email fetching, and sending.

Supports two credential sources:
  1. Local files: credentials.json + token.json (for local dev)
  2. Environment variables: GMAIL_CREDENTIALS_JSON + GMAIL_TOKEN_JSON (for CI/GitHub Actions)
"""

import base64
import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly",
          "https://www.googleapis.com/auth/gmail.send"]

PROJECT_DIR = Path(__file__).parent
CREDENTIALS_FILE = PROJECT_DIR / "credentials.json"
TOKEN_FILE = PROJECT_DIR / "token.json"


@dataclass
class EmailMessage:
    """Parsed email with body, metadata, and RFC822 Message-ID."""
    message_id: str           # Gmail's internal ID
    thread_id: str
    subject: str
    sender: str
    date: str
    snippet: str
    body_text: str = ""
    rfc822_message_id: str = ""  # For Apple Mail deep links
    label_ids: list[str] = field(default_factory=list)


def _write_env_credentials():
    """Write credentials from env vars to temp files if local files don't exist."""
    creds_json = os.getenv("GMAIL_CREDENTIALS_JSON", "")
    token_json = os.getenv("GMAIL_TOKEN_JSON", "")

    if creds_json and not CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.write_text(creds_json)

    if token_json and not TOKEN_FILE.exists():
        TOKEN_FILE.write_text(token_json)


class GmailClient:
    """Handles Gmail API authentication and email operations."""

    def __init__(self):
        self.service = None

    def authenticate(self):
        """Authenticate with Gmail API using OAuth2.

        Loads credentials from local files or environment variables.
        """
        _write_env_credentials()

        creds = None

        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                TOKEN_FILE.write_text(creds.to_json())
            else:
                if not CREDENTIALS_FILE.exists():
                    raise RuntimeError(
                        "No credentials available. Provide credentials.json locally "
                        "or set GMAIL_CREDENTIALS_JSON and GMAIL_TOKEN_JSON env vars."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CREDENTIALS_FILE), SCOPES
                )
                creds = flow.run_local_server(port=0)
                TOKEN_FILE.write_text(creds.to_json())

        self.service = build("gmail", "v1", credentials=creds)

    def fetch_emails(self, query: str, max_results: int = 50) -> list[EmailMessage]:
        """Fetch emails matching a Gmail search query."""
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        results = self.service.users().messages().list(
            userId="me", q=query, maxResults=max_results
        ).execute()

        messages = results.get("messages", [])
        if not messages:
            return []

        emails = []
        for msg_stub in messages:
            msg = self.service.users().messages().get(
                userId="me", id=msg_stub["id"], format="full"
            ).execute()
            email = self._parse_message(msg)
            if email:
                emails.append(email)

        return emails

    def send_html_email(self, to: str, subject: str, html_body: str):
        """Send an HTML email via Gmail API."""
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        message = MIMEText(html_body, "html")
        message["to"] = to
        message["subject"] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        self.service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()

    def _parse_message(self, msg: dict) -> Optional[EmailMessage]:
        """Parse a Gmail API message into an EmailMessage."""
        headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}

        body_text = self._extract_body(msg["payload"])

        return EmailMessage(
            message_id=msg["id"],
            thread_id=msg.get("threadId", ""),
            subject=headers.get("Subject", "(no subject)"),
            sender=headers.get("From", ""),
            date=headers.get("Date", ""),
            snippet=msg.get("snippet", ""),
            body_text=body_text,
            rfc822_message_id=headers.get("Message-ID", headers.get("Message-Id", "")),
            label_ids=msg.get("labelIds", []),
        )

    def _extract_body(self, payload: dict) -> str:
        """Recursively extract plain text body from a message payload."""
        if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

        parts = payload.get("parts", [])

        # Prefer text/plain
        for part in parts:
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")

        # Fall back to text/html, strip tags
        for part in parts:
            if part.get("mimeType") == "text/html" and part.get("body", {}).get("data"):
                html = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                return self._strip_html(html)

        # Recurse into multipart
        for part in parts:
            result = self._extract_body(part)
            if result:
                return result

        return ""

    @staticmethod
    def _strip_html(html: str) -> str:
        """Basic HTML tag stripping for fallback body extraction."""
        text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text
