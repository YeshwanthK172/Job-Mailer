import random
import re
import time

import pandas as pd
import streamlit as st

import config
import db
import email_sender
import email_writer
import eligibility
import contacts as contact_finder
import resume_parser
from models import Profile
from sources import adzuna, remoteok, greenhouse, lever

st.set_page_config(page_title="Job Mailer", page_icon="📬", layout="wide")
db.init()

ROLE_OPTIONS = [
    "Software Engineer", "Backend Developer", "Frontend Developer", "Full Stack Developer",
    "Data Analyst", "Data Scientist", "Machine Learning Engineer", "DevOps Engineer",
    "QA Engineer", "Test Engineer", "Business Analyst", "Product Manager",
    "UI/UX Designer", "Cloud Engineer", "Cybersecurity Analyst", "Intern", "Trainee",
]

DEFAULT_TEMPLATE = """Dear {hr_name},

I am {name}, a {grad_year} graduate, and I am writing to apply for the {role} position at {company}.

I have hands-on experience in the areas this role needs, and I would welcome the chance to contribute to your team. My resume is attached for your review, and the job posting I am applying to is here: {job_url}

Thank you for your time and consideration. I would be glad to share any further details.

Best regards,
{name}"""

for key, default in {"profile": None, "jobs": [], "drafts": []}.items():
    st.session_state.setdefault(key, default)

st.title("📬 Job Mailer")
st.caption("Find active openings, check your eligibility, reach the right HR contact, and apply by email.")

with st.sidebar:
    st.header("Settings")
    country = st.selectbox("Job-search country (Adzuna)", ["in", "us", "gb", "ca", "au", "sg", "de"], index=0)
    days = st.slider("Only jobs posted in the last N days", 3, 60, 14)
    min_score = st.slider("Minimum match score", 10, 90, 35)
    allow_remote = st.checkbox("Accept remote jobs regardless of location", value=True)
    st.divider()
    st.subheader("Sending limits")
    daily_cap = st.number_input("Max emails per day", 1, 100, 25)
    min_delay = st.number_input("Min seconds between emails", 5, 600, 20)
    max_delay = st.number_input("Max seconds between emails", 5, 900, 60)
    st.divider()
    st.caption("API keys are read from your .env file")
    st.write("Adzuna:", "✅" if config.ADZUNA_APP_ID else "➖ not set")
    st.write("Hunter:", "✅" if config.HUNTER_API_KEY else "➖ not set")
    st.write("Claude:", "✅" if config.ANTHROPIC_API_KEY else "➖ not set (optional)")

tab1, tab2, tab3, tab4 = st.tabs(["1 · Your profile", "2 · Find jobs", "3 · Review & send", "History"])

# ---------------------------------------------------------------- tab 1
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("Full name")
        from_email = st.text_input("Your email (From address)")
        app_password = st.text_input(
            "Email app password", type="password",
            help="For Gmail: Google Account > Security > 2-Step Verification > App passwords. "
                 "Kept in memory for this session only, never saved.",
        )
        current_role = st.text_input("Your current role / status", placeholder="e.g. Final-year B.Tech student")
        grad_year = st.number_input("Graduated / graduating year", 2000, 2035, 2026)
    with c2:
        target_roles = st.multiselect("Roles you are looking for", ROLE_OPTIONS)
        custom_roles = st.text_input("Other roles (comma separated)")
        locations = st.text_input("Preferred locations (comma separated)", placeholder="Chennai, Bengaluru, Remote")
        exp_years = st.number_input("Years of experience", 0.0, 40.0, 0.0, step=0.5)
        resume_file = st.file_uploader("Resume (PDF / DOCX / TXT)", type=["pdf", "docx", "txt"])
    exp_text = st.text_area("Job experience / projects (short summary)", height=120)
    template = st.text_area(
        "Email content  (placeholders: {hr_name} {company} {role} {name} {grad_year} {job_url})",
        value=DEFAULT_TEMPLATE, height=260,
    )
    use_ai = st.checkbox("Polish each email with Claude (needs ANTHROPIC_API_KEY)", value=False)

    b1, b2 = st.columns(2)
    if b1.button("Save profile", type="primary"):
        roles = target_roles + [r.strip() for r in custom_roles.split(",") if r.strip()]
        if not (name and from_email and roles and resume_file):
            st.error("Please fill name, email, at least one role, and upload your resume.")
        elif not re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+", from_email):
            st.error("That email address doesn't look valid.")
        else:
            data = resume_file.getvalue()
            text = resume_parser.extract_text(data, resume_file.name)
            st.session_state.profile = Profile(
                name=name, email=from_email, current_role=current_role, grad_year=int(grad_year),
                target_roles=roles, locations=[l.strip() for l in locations.split(",") if l.strip()],
                experience_years=float(exp_years), experience_text=exp_text, resume_text=text,
                resume_bytes=data, resume_name=resume_file.name,
                skills=resume_parser.extract_skills(text + " " + exp_text),
            )
            st.session_state.app_password = app_password
            st.session_state.template = template
            st.session_state.use_ai = use_ai
            st.success(f"Profile saved. Skills detected: {', '.join(st.session_state.profile.skills) or 'none'}")
    if b2.button("Test email login"):
        try:
            email_sender.test_login(from_email, app_password)
            st.success("Login worked.")
        except Exception as e:
            st.error(f"Login failed: {e}")

# ---------------------------------------------------------------- tab 2
with tab2:
    p = st.session_state.profile
    if not p:
        st.info("Save your profile first.")
    else:
        st.write("**Company career pages** (optional). Use the slug from the careers URL:")
        g1, g2 = st.columns(2)
        gh = g1.text_area("Greenhouse boards (one per line)", placeholder="e.g. airbnb\nstripe", height=90)
        lv = g2.text_area("Lever companies (one per line)", placeholder="e.g. netflix", height=90)
        if st.button("Search for active jobs", type="primary"):
            jobs = []
            with st.spinner("Searching..."):
                for role in p.target_roles:
                    for loc in (p.locations or [""]):
                        jobs += adzuna.search(role, loc, country, days)
                jobs += remoteok.search(p.target_roles, days)
                for t in [x.strip() for x in gh.splitlines() if x.strip()]:
                    jobs += greenhouse.fetch_board(t, days)
                for t in [x.strip() for x in lv.splitlines() if x.strip()]:
                    jobs += lever.fetch_board(t, days)
                seen, unique = set(), []
                for j in jobs:
                    k = j.url or (j.company + j.title)
                    if k not in seen:
                        seen.add(k)
                        unique.append(j)
                st.session_state.jobs = [eligibility.evaluate(j, p, allow_remote, min_score) for j in unique]
            st.success(f"Found {len(st.session_state.jobs)} jobs.")

        jobs = st.session_state.jobs
        if jobs:
            df = pd.DataFrame([{
                "Eligible": j.eligible, "Score": j.score, "Title": j.title, "Company": j.company,
                "Location": j.location, "Source": j.source, "Why": "; ".join(j.reasons), "Link": j.url,
            } for j in jobs]).sort_values(["Eligible", "Score"], ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True,
                         column_config={"Link": st.column_config.LinkColumn("Link")})
            st.caption("Remote listings from RemoteOK - https://remoteok.com")

        el = [j for j in jobs if j.eligible]
        if el:
            max_companies = st.number_input("Max companies to look up HR contacts for", 1, 50, 10,
                                            help="Hunter's free plan allows ~25 searches/month.")
            if st.button(f"Find HR contacts for {len(el)} eligible jobs"):
                drafts, done = [], set()
                with st.spinner("Looking up contacts..."):
                    for j in sorted(el, key=lambda x: -x.score):
                        if j.company in done:
                            continue
                        if len(done) >= max_companies:
                            break
                        done.add(j.company)
                        for c in contact_finder.find_hr_contacts(j.company):
                            body = email_writer.render(st.session_state.template, p, j, c)
                            if st.session_state.use_ai:
                                body = email_writer.ai_personalize(body, p, j)
                            drafts.append({"job": j, "contact": c, "subject": email_writer.subject_for(p, j),
                                           "body": body, "send": True})
                st.session_state.drafts = drafts
                st.success(f"Prepared {len(drafts)} draft emails. Go to the next tab.")

# ---------------------------------------------------------------- tab 3
with tab3:
    p = st.session_state.profile
    drafts = st.session_state.drafts
    if not drafts:
        st.info("No drafts yet. Find jobs and HR contacts first.")
    else:
        st.write(f"Sent today: **{db.sent_today()} / {daily_cap}**. Review every email before sending.")
        for i, d in enumerate(drafts):
            c, j = d["contact"], d["job"]
            dup = db.already_sent(c.email)
            label = f"{j.company} - {j.title}  ->  {c.email}" + ("  (already emailed)" if dup else "")
            with st.expander(label):
                d["send"] = st.checkbox("Send this one", value=d["send"] and not dup, key=f"s{i}", disabled=dup)
                d["subject"] = st.text_input("Subject", d["subject"], key=f"sub{i}")
                d["body"] = st.text_area("Body", d["body"], height=260, key=f"b{i}")
                st.caption(f"Contact: {c.name or 'unknown'} {c.position} (confidence {c.confidence}%) | Job: {j.url}")

        if st.button("Send selected emails", type="primary"):
            if not st.session_state.get("app_password"):
                st.error("Enter your email app password in the profile tab and save again.")
            else:
                todo = [d for d in drafts if d["send"] and not db.already_sent(d["contact"].email)]
                bar, log = st.progress(0.0), st.empty()
                for n, d in enumerate(todo, 1):
                    if db.sent_today() >= daily_cap:
                        st.warning("Daily cap reached. Stopping to protect your email account.")
                        break
                    c, j = d["contact"], d["job"]
                    try:
                        email_sender.send_email(p.email, st.session_state.app_password, c.email,
                                                d["subject"], d["body"], p.resume_bytes, p.resume_name)
                        db.log_sent(c.email, j.company, j.title, j.url, "sent")
                        log.success(f"Sent to {c.email} ({j.company})")
                    except Exception as e:
                        db.log_sent(c.email, j.company, j.title, j.url, f"failed: {e}")
                        log.error(f"Failed for {c.email}: {e}")
                    bar.progress(n / len(todo))
                    if n < len(todo):
                        time.sleep(random.uniform(min(min_delay, max_delay), max(min_delay, max_delay)))
                st.success("Done. See the History tab.")

# ---------------------------------------------------------------- tab 4
with tab4:
    rows = db.history()
    if rows:
        st.dataframe(pd.DataFrame(rows, columns=["Sent at", "Company", "Role", "Email", "Status"]),
                     use_container_width=True, hide_index=True)
    else:
        st.info("Nothing sent yet.")
