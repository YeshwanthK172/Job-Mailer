"""Rule-based eligibility check: role, skills, graduation year, experience, location."""
import re

from models import Job, Profile

TERM_MAP = {"intern": ["intern", "internship", "trainee"]}


def _role_match(job: Job, profile: Profile) -> bool:
    title = job.title.lower()
    for role in profile.target_roles:
        words = [w for w in re.split(r"\W+", role.lower()) if len(w) > 2]
        if words and all(w in title for w in words):
            return True
        if role.lower() in title:
            return True
    return False


def _location_ok(job: Job, profile: Profile, allow_remote: bool) -> bool:
    if not profile.locations:
        return True
    loc = job.location.lower()
    if allow_remote and "remote" in (loc + " " + job.title.lower()):
        return True
    return any(l.lower() in loc for l in profile.locations)


def _required_years(text: str):
    nums = [int(n) for n in re.findall(r"(\d{1,2})\s*\+?\s*(?:years|yrs|year)", text.lower())]
    nums = [n for n in nums if n <= 20]
    return min(nums) if nums else None


def _grad_years_mentioned(text: str):
    low = text.lower()
    pat = r"(20\d{2})\s*(?:batch|graduates?|pass[- ]?outs?|grads?)|(?:batch|class)\s*of\s*(20\d{2})"
    years = set()
    for m in re.finditer(pat, low):
        years.add(int(m.group(1) or m.group(2)))
    return years


def evaluate(job: Job, profile: Profile, allow_remote=True, min_score=35):
    text = f"{job.title}\n{job.description}"
    reasons, score, blocked = [], 0.0, False

    if _role_match(job, profile):
        score += 40
        reasons.append("Title matches a target role")
    else:
        blocked = True
        reasons.append("Title does not match any target role")

    if _location_ok(job, profile, allow_remote):
        score += 15
        reasons.append("Location OK")
    else:
        blocked = True
        reasons.append("Location outside your preferences")

    low = text.lower()
    matched = [s for s in profile.skills if re.search(r"(?<![a-z0-9])" + re.escape(s) + r"(?![a-z0-9])", low)]
    if profile.skills:
        ratio = len(matched) / max(len(profile.skills), 1)
        score += min(35, ratio * 100)
        if matched:
            reasons.append("Skills matched: " + ", ".join(matched[:8]))

    years = _grad_years_mentioned(text)
    if years:
        if profile.grad_year in years:
            score += 10
            reasons.append(f"Open to {profile.grad_year} graduates")
        else:
            blocked = True
            reasons.append(f"Targets {sorted(years)} graduates, not {profile.grad_year}")

    req = _required_years(text)
    if req is not None:
        if req <= profile.experience_years + 1:
            score += 10
            reasons.append(f"Experience requirement ({req}y) is within reach")
        else:
            blocked = True
            reasons.append(f"Needs {req}+ years experience, you have {profile.experience_years}")

    job.score = round(min(score, 100), 1)
    job.reasons = reasons
    job.eligible = (not blocked) and job.score >= min_score
    return job
