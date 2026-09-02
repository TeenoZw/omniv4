"""Admin activity log model."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import Column, Integer, String, Text, Uuid, event

from app.models import BaseModel

RETENTION_DAYS = 90


class AdminActivityLog(BaseModel):
    """Append-only activity records for admin operations."""

    __tablename__ = "admin_activity_logs"

    module = Column(String(80), nullable=False, index=True)
    change = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    actor_id = Column(Uuid(as_uuid=True), nullable=True, index=True)
    actor_name = Column(String(255), nullable=True)
    actor_email = Column(String(255), nullable=True, index=True)
    target_type = Column(String(80), nullable=True, index=True)
    target_id = Column(String(120), nullable=True, index=True)
    sequence_no = Column(Integer, nullable=False, index=True)
    previous_hash = Column(String(64), nullable=True)
    entry_hash = Column(String(64), nullable=False, unique=True, index=True)


@event.listens_for(AdminActivityLog, "before_update", propagate=True)
def _prevent_activity_update(*_args, **_kwargs):
    raise ValueError("admin_activity_logs is append-only and cannot be updated")


@event.listens_for(AdminActivityLog, "before_delete", propagate=True)
def _prevent_recent_activity_delete(_mapper, _connection, target: AdminActivityLog):
    """Allow deletes only for records older than retention window."""
    created_at = target.created_at
    if created_at is None:
        raise ValueError("admin_activity_logs cannot be deleted without timestamp")
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    if created_at >= cutoff:
        raise ValueError("admin_activity_logs cannot be deleted before retention window")
