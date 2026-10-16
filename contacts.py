"""Find HR / recruiting contacts via the Hunter.io API (verified, legitimate source)."""
import re

import requests

import config
import db
from models import Contact

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def find_hr_contacts(company: str, min_confidence: int = 70, limit: int = 2):
    cached = db.cached_contacts(company)
    if cached:
        return [c for c in cached if c.confidence >= min_confidence][:limit]
    if not config.HUNTER_API_KEY:
        return []
    try:
        r = requests.get(
            "https://api.hunter.io/v2/domain-search",
            params={
                "company": company,
                "department": "hr",
                "limit": 10,
                "api_key": config.HUNTER_API_KEY,
            },
            timeout=config.REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        emails = (r.json().get("data") or {}).get("emails", [])
    except Exception:
        return []
    found = []
    for e in emails:
        name = " ".join(x for x in [e.get("first_name"), e.get("last_name")] if x)
        found.append(
            Contact(
                company=company,
                email=e.get("value", ""),
                name=name,
                position=e.get("position") or "",
                confidence=int(e.get("confidence") or 0),
            )
        )
    db.cache_contacts(found)
    found.sort(key=lambda c: c.confidence, reverse=True)
    return [c for c in found if c.confidence >= min_confidence][:limit]


def scrape_published_email(page_url: str):
    """Fallback: look for an email address the company itself published on a page
    (e.g. 'send your CV to careers@...'). Only reads the single page you give it."""
    try:
        r = requests.get(page_url, headers={"User-Agent": config.USER_AGENT}, timeout=config.REQUEST_TIMEOUT)
        r.raise_for_status()
    except Exception:
        return []
    hits = set(EMAIL_RE.findall(r.text))
    good = [e for e in hits if any(k in e.lower() for k in ("career", "jobs", "hr", "recruit", "talent", "hiring"))]
    return sorted(good)
