import os
from dotenv import load_dotenv

load_dotenv()

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

DB_PATH = os.getenv("JOBMAILER_DB", "jobmailer.db")
REQUEST_TIMEOUT = 20
USER_AGENT = "JobMailer/1.0 (personal job-search tool)"
