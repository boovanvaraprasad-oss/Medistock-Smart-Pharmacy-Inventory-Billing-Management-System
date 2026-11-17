import os
from pathlib import Path

from dotenv import load_dotenv

# Load backend/.env regardless of current working directory
_env_path = Path(__file__).resolve().parents[2] / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)
load_dotenv()

# MongoDB
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ACCESS_EXPIRY_MIN = int(
    os.getenv("JWT_ACCESS_EXPIRY_MIN", "20")
)

# SMTP Mailer Settings
def get_smtp_settings():
    """Dynamically read the latest SMTP settings from backend/.env."""
    prev_db_name = os.environ.get("DATABASE_NAME")
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path, override=True)
    if prev_db_name:
        os.environ["DATABASE_NAME"] = prev_db_name
    host = (os.getenv("SMTP_HOST") or "").strip()
    try:
        port = int((os.getenv("SMTP_PORT") or "587").strip() or 587)
    except ValueError:
        port = 587
    user = (os.getenv("SMTP_USER") or "").strip()
    password = (os.getenv("SMTP_PASSWORD") or "").strip()
    # Automatically strip spaces from Gmail App Passwords (e.g. "tbro vopw gyzu ymam" -> "tbrovopwgyzuzymam")
    if "gmail.com" in host.lower():
        password = password.replace(" ", "")
    from_email = (os.getenv("SMTP_FROM_EMAIL") or "").strip() or user or "noreply@medistock.com"
    from_name = (os.getenv("SMTP_FROM_NAME") or "MediStock Healthcare").strip()
    tls = (os.getenv("SMTP_TLS") or "true").strip().lower() in ("true", "1", "yes")
    ssl = (os.getenv("SMTP_SSL") or "false").strip().lower() in ("true", "1", "yes")
    admin_email = (os.getenv("SMTP_ADMIN_EMAIL") or "").strip() or "support@medistock.com"
    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "from_email": from_email,
        "from_name": from_name,
        "tls": tls,
        "ssl": ssl,
        "admin_email": admin_email,
        "configured": bool(host and (user or host in ("localhost", "127.0.0.1")) and password),
    }

# Fallback module constants
_initial_smtp = get_smtp_settings()
SMTP_HOST = _initial_smtp["host"]
SMTP_PORT = _initial_smtp["port"]
SMTP_USER = _initial_smtp["user"]
SMTP_PASSWORD = _initial_smtp["password"]
SMTP_FROM_EMAIL = _initial_smtp["from_email"]
SMTP_FROM_NAME = _initial_smtp["from_name"]
SMTP_TLS = _initial_smtp["tls"]
SMTP_SSL = _initial_smtp["ssl"]
SMTP_ADMIN_EMAIL = _initial_smtp["admin_email"]

