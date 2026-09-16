from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes.api import api_router

app = FastAPI()

app.include_router(api_router, prefix="/api/v1")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

# Keep this mount after the API routes so /api/v1 requests reach FastAPI first.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
