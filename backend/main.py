from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.indexes import create_indexes
from app.routes.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # This code runs once, when the server starts
    await create_indexes()

    yield

    # (Code placed after yield would run when the server stops)


app = FastAPI(
    title="MediStock API",
    lifespan=lifespan,
)


# API routes

app.include_router(
    api_router,
    prefix="/api/v1",
)


# Frontend

FRONTEND_DIR = (
    Path(__file__).resolve().parent.parent / "frontend"
)


# Keep this mount after the API routes
# so /api/v1 requests reach FastAPI first.

app.mount(
    "/",
    StaticFiles(
        directory=FRONTEND_DIR,
        html=True,
    ),
    name="frontend",
)