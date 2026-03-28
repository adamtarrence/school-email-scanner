"""
Fetch linked content from notification emails.

Used to supplement emails where the actual content is on an external page
rather than in the email body (e.g. "Spencer's teacher posted an assignment").
"""
import re
import urllib.request
import urllib.error
from html.parser import HTMLParser
from typing import Optional


# Domains that always require login — skip fetch entirely
_LOGIN_REQUIRED_DOMAINS = [
    "schoology.com",
    "instructure.com",   # Canvas
    "parentsquare.com",
    "seesaw.me",
    "powerschool.com",
    "blackboard.com",
    "remind.com",
    "bloomz.net",
    "google.com/forms",  # Forms require sign-in to see responses
    "docs.google.com",
    "drive.google.com",
]

# URL fragments that indicate tracking/utility links — skip these
_SKIP_URL_FRAGMENTS = [
    "unsubscribe", "optout", "click.icptrack", "mailchimp.com/track",
    "list-manage", "open.aspx", "/track/", "click?",
]

# Signals that a fetched page is a login wall
_LOGIN_WALL_SIGNALS = [
    "sign in to", "log in to", "please log in", "please sign in",
    "login required", "authentication required", "forgot your password",
    "create an account", "don't have an account",
]


class _TextExtractor(HTMLParser):
    """Strip HTML tags and return readable text."""

    def __init__(self):
        super().__init__()
        self._parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "footer", "header"):
            self._skip = True
        if tag in ("p", "h1", "h2", "h3", "h4", "h5", "li"):
            self._parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "footer", "header"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            stripped = data.strip()
            if stripped:
                self._parts.append(stripped)

    def get_text(self) -> str:
        return " ".join(self._parts)[:3000]


def extract_first_url(text: str) -> Optional[str]:
    """Return the first meaningful http(s) URL from plain text."""
    for url in re.findall(r'https?://[^\s<>"\']+', text):
        url = url.rstrip(".,;)")
        if not any(frag in url.lower() for frag in _SKIP_URL_FRAGMENTS):
            return url
    return None


def is_login_required(url: str) -> bool:
    """True if the URL is a known login-gated domain."""
    lower = url.lower()
    return any(domain in lower for domain in _LOGIN_REQUIRED_DOMAINS)


def fetch_linked_content(url: str, timeout: int = 6) -> tuple[str, bool]:
    """
    Attempt to fetch readable text from a URL.

    Returns:
        (content, requires_login)
        - content: extracted text, or "" on failure
        - requires_login: True if the page is behind a login wall
    """
    if is_login_required(url):
        return "", True

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; SchoolSkim/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "html" not in content_type:
                return "", False
            html = resp.read(80000).decode("utf-8", errors="ignore")

        # Detect login wall by signal density in the page text
        html_lower = html.lower()
        login_hits = sum(1 for sig in _LOGIN_WALL_SIGNALS if sig in html_lower)
        if login_hits >= 2:
            return "", True

        parser = _TextExtractor()
        parser.feed(html)
        content = parser.get_text().strip()
        return content, False

    except Exception:
        return "", False
