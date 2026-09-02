"""Health check routes."""
from sqlalchemy import text

from fastapi import APIRouter
from app.core.database import SessionLocal

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    return {"status": "ready"}


@router.get("/health/db")
async def database_health_check():
    """Database connectivity check."""
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    finally:
        db.close()
