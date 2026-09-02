"""API routes package."""
from . import health
from . import users
from . import hubs
from . import devices
from . import enquiries
from . import admin
from . import auth
from . import technician_jobs
from . import compliance

__all__ = [
    "health",
    "users",
    "hubs",
    "devices",
    "enquiries",
    "admin",
    "auth",
    "technician_jobs",
    "compliance",
]
