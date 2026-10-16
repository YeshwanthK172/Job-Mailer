# Job Mailer

Streamlit app that finds actively hiring jobs, checks your eligibility, looks up HR contacts,
and sends your application from your own email.

## Setup
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then add your keys
streamlit run app.py
```

## Keys (all free tiers)
| Key | Purpose | Where |
|---|---|---|
| ADZUNA_APP_ID / ADZUNA_APP_KEY | Job search | https://developer.adzuna.com |
| HUNTER_API_KEY | HR email lookup | https://hunter.io/api |
| ANTHROPIC_API_KEY | Optional email polishing | https://console.anthropic.com |

Without Adzuna you still get RemoteOK plus any Greenhouse/Lever company boards you list.

## Sending from Gmail
Turn on 2-Step Verification, then create an **App Password**
(Google Account > Security > App passwords) and paste it in the app. Your normal password won't work.
The app password is held in memory only and never written to disk.

## How it works
1. **Profile**: your details, resume, roles, locations, email template
2. **Find jobs**: Adzuna, RemoteOK, Greenhouse, Lever; filtered by freshness
3. **Eligibility**: role, location, skills, graduation year and experience rules
4. **Contacts**: HR emails from Hunter.io (cached in SQLite)
5. **Review & send**: you approve every email; daily cap, random delays, no duplicates

## Why it is built this way
- No LinkedIn scraping: it violates their terms and gets accounts banned.
- No random email harvesting: it risks breaching privacy and anti-spam laws (GDPR, DPDP, CAN-SPAM).
- Manual review plus a daily cap keeps your mailbox from being flagged as spam.
- Every email includes an opt-out line; honour any request to stop.

## Layout
```
app.py            Streamlit UI
config.py         env/API keys
models.py         Profile, Job, Contact
db.py             SQLite (sent log, contact cache)
resume_parser.py  PDF/DOCX text + skill extraction
eligibility.py    match scoring and hard filters
contacts.py       Hunter.io lookup
email_writer.py   template fill + optional Claude polish
email_sender.py   SMTP sending with attachment
sources/          adzuna, remoteok, greenhouse, lever
```
