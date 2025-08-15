# helpers.py
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


# --- CONFIG ---
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
IPA_HOST = "https://ldap."
IPA_USER = "admin"
IPA_PASS = os.getenv("PWD", "")
IPA_CA = DATA_DIR / "ipa-ca.crt"
USERS_CSV_PATH = DATA_DIR / "from_db.csv"
DEPS_CSV_PATH = DATA_DIR / "deps.csv"
JSON_URL = f"{IPA_HOST}/ipa/session/json"
LOGIN_URL = f"{IPA_HOST}/ipa/session/login_password"
# ---------------------