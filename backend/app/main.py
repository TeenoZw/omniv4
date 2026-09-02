"""Main FastAPI application."""
import logging

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.api.routes import (
    health,
    users,
    hubs,
    devices,
    enquiries,
    admin,
    auth,
    technician_jobs,
    compliance,
)
from app.models.user import User, UserRole
from app.models import Base
from app.services.admin_activity import ensure_admin_activity_guards, prune_admin_activity

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

logger = logging.getLogger(__name__)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_origin_regex=settings.allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(hubs.router, prefix="/api/v1/hubs", tags=["hubs"])
app.include_router(devices.router, prefix="/api/v1", tags=["devices"])
app.include_router(enquiries.router, prefix="/api/v1/enquiries", tags=["enquiries"])
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(technician_jobs.router, prefix="/api/v1", tags=["technician-jobs"])
app.include_router(compliance.router, prefix="/api/v1", tags=["compliance"])


@app.exception_handler(OperationalError)
async def sqlalchemy_operational_error_handler(_: Request, exc: OperationalError):
    """Return a deterministic error when the database is unreachable."""
    logger.exception("Database operational error: %s", exc)
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Database unavailable. Start the database service and retry.",
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(_: Request, exc: SQLAlchemyError):
    """Return a consistent persistence error payload."""
    logger.exception("Database error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Database request failed.",
        },
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Omni Logistics API",
        "version": settings.app_version,
        "docs": "/docs",
    }


@app.on_event("startup")
def ensure_bootstrap_admin() -> None:
    """Ensure the default Omni admin account exists for initial deployment access."""
    if settings.auto_create_schema:
        Base.metadata.create_all(bind=engine)

    try:
        ensure_admin_activity_guards(engine)
    except Exception as exc:  # pragma: no cover - startup guard
        logger.warning("Unable to apply admin activity guards: %s", exc)

    db = SessionLocal()
    try:
        prune_admin_activity(db)

        if not settings.bootstrap_admin_password:
            logger.info("Bootstrap admin password not set; skipping bootstrap admin creation.")
            return

        existing = db.query(User).filter(User.email == settings.bootstrap_admin_email).first()
        if existing:
            if existing.role != UserRole.admin:
                existing.role = UserRole.admin
            if not existing.is_active:
                existing.is_active = True
            db.add(existing)
            db.commit()
            return

        admin_user = User(
            name="Omni Super Admin",
            email=settings.bootstrap_admin_email,
            hashed_password=get_password_hash(settings.bootstrap_admin_password),
            role=UserRole.admin,
            is_active=True,
            is_verified=True,
        )
        db.add(admin_user)
        db.commit()
        logger.info("Bootstrap admin account ensured for %s", settings.bootstrap_admin_email)
    except Exception as exc:  # pragma: no cover - startup guard
        db.rollback()
        logger.warning("Unable to ensure bootstrap admin account: %s", exc)
    finally:
        db.close()
