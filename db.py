"""SQLite storage: what was sent (so nobody is emailed twice) + contact cache."""
import sqlite3
from datetime import datetime, date

import config


def _conn():
    return sqlite3.connect(config.DB_PATH)


def init():
    with _conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS sent (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT, company TEXT, role TEXT, job_url TEXT,
                status TEXT, sent_at TEXT)"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS contacts (
                company TEXT, email TEXT, name TEXT, position TEXT,
                confidence INTEGER, UNIQUE(company, email))"""
        )


def already_sent(email: str) -> bool:
    with _conn() as c:
        row = c.execute(
            "SELECT 1 FROM sent WHERE lower(email)=lower(?) AND status='sent'", (email,)
        ).fetchone()
    return row is not None


def log_sent(email, company, role, job_url, status):
    with _conn() as c:
        c.execute(
            "INSERT INTO sent (email, company, role, job_url, status, sent_at) VALUES (?,?,?,?,?,?)",
            (email, company, role, job_url, status, datetime.now().isoformat(timespec="seconds")),
        )


def sent_today() -> int:
    today = date.today().isoformat()
    with _conn() as c:
        row = c.execute(
            "SELECT COUNT(*) FROM sent WHERE status='sent' AND sent_at LIKE ?", (today + "%",)
        ).fetchone()
    return row[0]


def history():
    with _conn() as c:
        return c.execute(
            "SELECT sent_at, company, role, email, status FROM sent ORDER BY id DESC LIMIT 500"
        ).fetchall()


def cache_contacts(contacts):
    with _conn() as c:
        for k in contacts:
            c.execute(
                "INSERT OR REPLACE INTO contacts VALUES (?,?,?,?,?)",
                (k.company.lower(), k.email, k.name, k.position, k.confidence),
            )


def cached_contacts(company: str):
    from models import Contact

    with _conn() as c:
        rows = c.execute(
            "SELECT company,email,name,position,confidence FROM contacts WHERE company=?",
            (company.lower(),),
        ).fetchall()
    return [Contact(*r) for r in rows]
