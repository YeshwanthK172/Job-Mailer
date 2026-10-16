"""Lever public postings. Company slug = the slug in jobs.lever.co/<slug>."""
from datetime import datetime, timezone

import requests

import config
from models import Job
from ._util import cutoff


def fetch_board(slug: str, days: int = 30):
    try:
        r = requests.get(
            f"https://api.lever.co/v0/postings/{slug}",
            params={"mode": "json"},
            timeout=config.REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        postings = r.json()
    except Exception:
        return []
    out, limit = [], cutoff(days)
    for p in postings:
        created = p.get("createdAt")
        dt = datetime.fromtimestamp(created / 1000, tz=timezone.utc) if created else None
        if dt and dt < limit:
            continue
        out.append(
            Job(
                title=p.get("text", ""),
                company=slug.replace("-", " ").title(),
                location=(p.get("categories") or {}).get("location", ""),
                url=p.get("hostedUrl", ""),
                description=p.get("descriptionPlain", ""),
                source="Lever",
                posted=dt.isoformat() if dt else "",
            )
        )
    return out
