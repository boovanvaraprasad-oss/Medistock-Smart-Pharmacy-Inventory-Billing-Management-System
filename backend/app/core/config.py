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
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "") or SMTP_USER or "noreply@medistock.com"
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "MediStock Healthcare")
SMTP_TLS = os.getenv("SMTP_TLS", "true").lower() in ("true", "1", "yes")
SMTP_SSL = os.getenv("SMTP_SSL", "false").lower() in ("true", "1", "yes")
SMTP_ADMIN_EMAIL = os.getenv("SMTP_ADMIN_EMAIL", "") or "support@medistock.com"
