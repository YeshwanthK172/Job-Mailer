"""Greenhouse public job boards. Board token = the slug in boards.greenhouse.io/<token>."""
import requests

import config
from models import Job
from ._util import strip_html, cutoff, parse_iso


def fetch_board(token: str, days: int = 30):
    try:
        r = requests.get(
            f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs",
            params={"content": "true"},
            timeout=config.REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        jobs = r.json().get("jobs", [])
    except Exception:
        return []
    out, limit = [], cutoff(days)
    for j in jobs:
        dt = parse_iso(j.get("updated_at", ""))
        if dt and dt < limit:
            continue
        out.append(
            Job(
                title=j.get("title", ""),
                company=token.replace("-", " ").title(),
                location=(j.get("location") or {}).get("name", ""),
                url=j.get("absolute_url", ""),
                description=strip_html(j.get("content", "")),
                source="Greenhouse",
                posted=j.get("updated_at", ""),
            )
        )
    return out
