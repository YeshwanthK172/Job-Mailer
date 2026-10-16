"""RemoteOK public JSON feed (remote jobs). Please keep the attribution link in your UI."""
import requests

import config
from models import Job
from ._util import strip_html, cutoff, parse_iso


def search(roles: list, days: int = 14):
    try:
        r = requests.get(
            "https://remoteok.com/api",
            headers={"User-Agent": config.USER_AGENT},
            timeout=config.REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        items = [i for i in r.json() if isinstance(i, dict) and i.get("position")]
    except Exception:
        return []
    out, limit = [], cutoff(days)
    for j in items:
        title = j.get("position", "")
        blob = (title + " " + " ".join(j.get("tags", []))).lower()
        if not any(any(w in blob for w in role.lower().split()) for role in roles):
            continue
        dt = parse_iso(j.get("date", ""))
        if dt and dt < limit:
            continue
        out.append(
            Job(
                title=title,
                company=j.get("company", "Unknown"),
                location=j.get("location") or "Remote",
                url=j.get("url", ""),
                description=strip_html(j.get("description", "")),
                source="RemoteOK",
                posted=j.get("date", ""),
            )
        )
    return out
