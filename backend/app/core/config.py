import os

from dotenv import load_dotenv

load_dotenv()

# MongoDB
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ACCESS_EXPIRY_MIN = int(
    os.getenv("JWT_ACCESS_EXPIRY_MIN", "20")
)