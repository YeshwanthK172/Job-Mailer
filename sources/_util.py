import html
import re
from datetime import datetime, timedelta, timezone


def strip_html(s: str) -> str:
    s = html.unescape(s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def cutoff(days: int):
    return datetime.now(timezone.utc) - timedelta(days=days)


def parse_iso(s: str):
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None
