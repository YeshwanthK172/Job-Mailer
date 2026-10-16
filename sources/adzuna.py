"""Adzuna job search API (free key): https://developer.adzuna.com/"""
import requests

import config
from models import Job
from ._util import strip_html


def search(role: str, location: str, country: str = "in", days: int = 14, limit: int = 30):
    if not (config.ADZUNA_APP_ID and config.ADZUNA_APP_KEY):
        return []
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {
        "app_id": config.ADZUNA_APP_ID,
        "app_key": config.ADZUNA_APP_KEY,
        "results_per_page": limit,
        "what": role,
        "max_days_old": days,
        "content-type": "application/json",
    }
    if location:
        params["where"] = location
    try:
        r = requests.get(url, params=params, timeout=config.REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json().get("results", [])
    except Exception:
        return []
    return [
        Job(
            title=j.get("title", ""),
            company=(j.get("company") or {}).get("display_name", "Unknown"),
            location=(j.get("location") or {}).get("display_name", ""),
            url=j.get("redirect_url", ""),
            description=strip_html(j.get("description", "")),
            source="Adzuna",
            posted=j.get("created", ""),
        )
        for j in data
    ]
