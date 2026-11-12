"""
Shared pytest fixtures for MediStock integration tests.

Strategy
--------
* Uses a separate MongoDB database (medistock_test) so the live database
  is never touched.
* Patches app.core.database.db and app.core.database.client before the
  FastAPI app is imported, so every service and route uses the test DB.
* Each test function gets a fresh, empty database via the `clean_db`
  fixture (autouse at the function scope).
* An AsyncClient wrapping the FastAPI app is provided by `client`.
  No running server is needed.
"""

import os
import pytest
import pytest_asyncio
from dotenv import load_dotenv

# ------------------------------------------------------------------
# Point to the test database BEFORE importing anything from the app.
# ------------------------------------------------------------------
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
os.environ["DATABASE_NAME"] = "medistock_test"
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_for_pytest_only")
os.environ.setdefault("JWT_ACCESS_EXPIRY_MIN", "20")

import app.core.database as _db_module  # noqa: E402
_test_db = _db_module.db

from httpx import AsyncClient, ASGITransport  # noqa: E402
from main import app  # noqa: E402


# ------------------------------------------------------------------
# Collections that are wiped between every test
# ------------------------------------------------------------------
_TEST_COLLECTIONS = [
    "users",
    "login_attempts",
    "revoked_tokens",
    "audit_logs",
    "notification_reads",
    "categories",
    "manufacturers",
    "suppliers",
    "units",
    "medicines",
    "stock_batches",
    "stock_transactions",
    "purchase_orders",
    "purchase_items",
    "bills",
    "bill_items",
    "bill_returns",
    "settings",
    "counters",
]


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    """Wipe every test collection before each test in parallel."""
    import asyncio
    await asyncio.gather(*[_test_db[name].delete_many({}) for name in _TEST_COLLECTIONS])
    yield


@pytest_asyncio.fixture
async def client():
    """Return an async HTTP test client backed by the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ------------------------------------------------------------------
# Helper: register the first (owner) user via the public signup route
# ------------------------------------------------------------------
async def register_owner(client, email="owner@medistock.com", password="OwnerPass1!"):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


async def login(client, email, password):
    resp = await client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def auth_headers(client, email="owner@medistock.com", password="OwnerPass1!"):
    token = await login(client, email, password)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def owner_headers(client):
    """Register the first owner and return auth headers."""
    await register_owner(client)
    return await auth_headers(client)


@pytest_asyncio.fixture
async def owner_token(client):
    """Return raw access token for the auto-registered owner."""
    await register_owner(client)
    return await login(client, "owner@medistock.com", "OwnerPass1!")

