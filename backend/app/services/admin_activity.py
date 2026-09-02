"""Admin activity log helpers."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models.admin_activity import AdminActivityLog
from app.models.user import User

RETENTION_DAYS = 90


def append_admin_activity(
    db: Session,
    *,
    module: str,
    change: str,
    details: Optional[str] = None,
    actor: Optional[User] = None,
    actor_name: Optional[str] = None,
    actor_email: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
) -> None:
    """Persist an activity record without breaking caller flow on logging errors."""
    try:
        previous_entry = (
            db.query(AdminActivityLog)
            .order_by(AdminActivityLog.sequence_no.desc())
            .first()
        )
        sequence_no = (previous_entry.sequence_no if previous_entry else 0) + 1
        previous_hash = previous_entry.entry_hash if previous_entry else None
        created_at = datetime.now(timezone.utc)
        payload = {
            "sequence_no": sequence_no,
            "created_at": created_at.isoformat(),
            "module": module,
            "change": change,
            "details": details,
            "actor_id": str(actor.id) if actor else None,
            "actor_name": actor.name if actor else actor_name,
            "actor_email": actor.email if actor else actor_email,
            "target_type": target_type,
            "target_id": target_id,
            "previous_hash": previous_hash,
        }
        entry_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest()

        entry = AdminActivityLog(
            created_at=created_at,
            module=module,
            change=change,
            details=details,
            actor_id=actor.id if actor else None,
            actor_name=actor.name if actor else actor_name,
            actor_email=actor.email if actor else actor_email,
            target_type=target_type,
            target_id=target_id,
            sequence_no=sequence_no,
            previous_hash=previous_hash,
            entry_hash=entry_hash,
        )
        db.add(entry)
        db.commit()
    except Exception:
        db.rollback()


def prune_admin_activity(db: Session) -> None:
    """Delete records older than retention period."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    try:
        db.query(AdminActivityLog).filter(AdminActivityLog.created_at < cutoff).delete()
        db.commit()
    except Exception:
        db.rollback()


def verify_admin_activity_integrity(db: Session, limit: int = 500) -> dict:
    """Validate hash-chain continuity for the most recent activity rows."""
    rows = (
        db.query(AdminActivityLog)
        .order_by(AdminActivityLog.sequence_no.desc())
        .limit(limit)
        .all()
    )
    if not rows:
        return {"ok": True, "checked": 0, "issues": []}

    ordered = list(reversed(rows))
    issues: list[dict] = []
    previous_hash: Optional[str] = None
    previous_sequence: Optional[int] = None

    for index, row in enumerate(ordered):
        created_at = row.created_at
        if created_at is None:
            issues.append({"id": str(row.id), "reason": "missing_created_at"})
            continue
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        # When verifying a limited trailing window, the first row in the slice
        # may legitimately point to an earlier record outside the result set.
        if index > 0:
            assert previous_sequence is not None
            if row.sequence_no != previous_sequence + 1:
                issues.append(
                    {
                        "id": str(row.id),
                        "reason": "sequence_gap",
                        "expected": previous_sequence + 1,
                        "actual": row.sequence_no,
                    }
                )

            if row.previous_hash != previous_hash:
                issues.append(
                    {
                        "id": str(row.id),
                        "reason": "previous_hash_mismatch",
                        "expected": previous_hash,
                        "actual": row.previous_hash,
                    }
                )

        payload = {
            "sequence_no": row.sequence_no,
            "created_at": created_at.isoformat(),
            "module": row.module,
            "change": row.change,
            "details": row.details,
            "actor_id": str(row.actor_id) if row.actor_id else None,
            "actor_name": row.actor_name,
            "actor_email": row.actor_email,
            "target_type": row.target_type,
            "target_id": row.target_id,
            "previous_hash": row.previous_hash,
        }
        expected_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest()
        if row.entry_hash != expected_hash:
            issues.append(
                {
                    "id": str(row.id),
                    "reason": "entry_hash_mismatch",
                }
            )

        previous_hash = row.entry_hash
        previous_sequence = row.sequence_no

    valid = len(issues) == 0
    return {"ok": valid, "valid": valid, "checked": len(ordered), "issues": issues}


def ensure_admin_activity_guards(engine: Engine) -> None:
    """Install DB-level guards that keep activity logs append-only."""
    dialect = engine.dialect.name
    if dialect == "sqlite":
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TRIGGER IF NOT EXISTS trg_admin_activity_no_update
                    BEFORE UPDATE ON admin_activity_logs
                    BEGIN
                        SELECT RAISE(ABORT, 'admin_activity_logs is immutable');
                    END;
                    """
                )
            )
            conn.execute(
                text(
                    f"""
                    CREATE TRIGGER IF NOT EXISTS trg_admin_activity_no_recent_delete
                    BEFORE DELETE ON admin_activity_logs
                    BEGIN
                        SELECT CASE
                            WHEN OLD.created_at >= datetime('now', '-{RETENTION_DAYS} days')
                            THEN RAISE(ABORT, 'admin_activity_logs cannot be deleted before retention window')
                        END;
                    END;
                    """
                )
            )
        return

    if dialect.startswith("postgres"):
        with engine.begin() as conn:
            conn.execute(
                text(
                    f"""
                    CREATE OR REPLACE FUNCTION prevent_admin_activity_mutation() RETURNS trigger AS $$
                    BEGIN
                        IF TG_OP = 'UPDATE' THEN
                            RAISE EXCEPTION 'admin_activity_logs is immutable';
                        END IF;
                        IF TG_OP = 'DELETE' AND OLD.created_at >= (NOW() - INTERVAL '{RETENTION_DAYS} days') THEN
                            RAISE EXCEPTION 'admin_activity_logs cannot be deleted before retention window';
                        END IF;
                        RETURN OLD;
                    END;
                    $$ LANGUAGE plpgsql;
                    """
                )
            )
            conn.execute(text("DROP TRIGGER IF EXISTS trg_admin_activity_immutable ON admin_activity_logs;"))
            conn.execute(
                text(
                    """
                    CREATE TRIGGER trg_admin_activity_immutable
                    BEFORE UPDATE OR DELETE ON admin_activity_logs
                    FOR EACH ROW EXECUTE FUNCTION prevent_admin_activity_mutation();
                    """
                )
            )
