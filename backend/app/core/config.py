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