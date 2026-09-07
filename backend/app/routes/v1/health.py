from fastapi import APIRouter
from app.core.database import db

router= APIRouter()

@router.get("/health")
async def health_check():
    return {"status":"ok"}

@router.get("/health/readiness")
async def readiness_check():
    await db.command("ping")
    return {"status":"ready"}