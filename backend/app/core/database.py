from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import MONGO_URI, DATABASE_NAME

client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]
