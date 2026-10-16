"""Fill the user's template per company/role, optionally polish with Claude."""
import config
from models import Job, Profile, Contact

FOOTER = (
    "\n\n--\nIf you'd rather not receive further emails from me, just reply "
    "with \"unsubscribe\" and I won't write again."
)


def render(template: str, profile: Profile, job: Job, contact: Contact) -> str:
    first = contact.name.split()[0] if contact.name else "Hiring Team"
    greeting_name = first if contact.name else "Hiring Team"
    body = (
        template.replace("{hr_name}", greeting_name)
        .replace("{company}", job.company)
        .replace("{role}", job.title)
        .replace("{name}", profile.name)
        .replace("{grad_year}", str(profile.grad_year))
        .replace("{job_url}", job.url)
    )
    return body.strip() + FOOTER


def subject_for(profile: Profile, job: Job) -> str:
    return f"Application for {job.title} - {profile.name}"


def ai_personalize(body: str, profile: Profile, job: Job):
    """Optional. Returns the improved body, or the original if the API isn't set up."""
    if not config.ANTHROPIC_API_KEY:
        return body
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        prompt = (
            "Lightly rewrite this job-application email so it sounds natural and mentions "
            f"why the candidate fits the '{job.title}' role at {job.company}. Keep it under 150 words, "
            "keep the sign-off and the unsubscribe footer, do not invent facts.\n\n"
            f"Job description excerpt:\n{job.description[:1500]}\n\n"
            f"Candidate skills: {', '.join(profile.skills)}\n"
            f"Candidate experience: {profile.experience_text[:600]}\n\n"
            f"Email:\n{body}\n\nReturn only the email body."
        )
        msg = client.messages.create(
            model="claude-sonnet-5-5",
            max_tokens=700,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception:
        return body
