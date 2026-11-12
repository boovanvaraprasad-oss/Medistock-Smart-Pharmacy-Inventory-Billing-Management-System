import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import MONGO_URI, DATABASE_NAME

_clients: dict = {}


def _get_client():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop not in _clients:
        uri = os.getenv("MONGO_URI", MONGO_URI)
        _clients[loop] = AsyncIOMotorClient(uri)
    return _clients[loop]


def _get_db():
    cl = _get_client()
    db_name = os.getenv("DATABASE_NAME", DATABASE_NAME)
    return cl[db_name]


class _DatabaseProxy:
    def __getattr__(self, name: str):
        return getattr(_get_db(), name)

    def __getitem__(self, name: str):
        return _get_db()[name]


class _ClientProxy:
    def __getattr__(self, name: str):
        return getattr(_get_client(), name)

    def __getitem__(self, name: str):
        return _get_client()[name]


client = _ClientProxy()
db = _DatabaseProxy()

