"""Refresh token issuance, validation, rotation, and revocation helpers."""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.refresh_token import RefreshToken
from app.models.user import User


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _build_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def issue_refresh_token(
    db: Session,
    user: User,
    *,
    issued_ip: Optional[str] = None,
    issued_user_agent: Optional[str] = None,
) -> tuple[str, RefreshToken]:
    raw_token = secrets.token_urlsafe(settings.refresh_token_entropy_bytes)
    token_record = RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(raw_token),
        expires_at=_build_expiry(),
        issued_ip=issued_ip,
        issued_user_agent=issued_user_agent,
        is_active=True,
    )
    db.add(token_record)
    db.flush()
    return raw_token, token_record


def get_valid_refresh_token(db: Session, raw_token: str) -> Optional[RefreshToken]:
    token_hash = _hash_token(raw_token)
    record = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )
    if not record:
        return None
    now = datetime.now(timezone.utc)
    if not record.is_active or record.revoked_at is not None:
        return None
    if _as_utc(record.expires_at) < now:
        record.is_active = False
        record.revoked_at = now
        record.revoked_reason = "expired"
        db.add(record)
        db.flush()
        return None
    return record


def revoke_refresh_token(
    db: Session,
    record: RefreshToken,
    *,
    reason: str = "logout",
) -> RefreshToken:
    if record.revoked_at is None:
        record.revoked_at = datetime.now(timezone.utc)
    record.revoked_reason = reason
    record.is_active = False
    db.add(record)
    db.flush()
    return record


def rotate_refresh_token(
    db: Session,
    old_record: RefreshToken,
    user: User,
    *,
    issued_ip: Optional[str] = None,
    issued_user_agent: Optional[str] = None,
) -> tuple[str, RefreshToken]:
    raw_token, new_record = issue_refresh_token(
        db,
        user,
        issued_ip=issued_ip,
        issued_user_agent=issued_user_agent,
    )
    revoke_refresh_token(db, old_record, reason="rotated")
    old_record.rotated_to_token_id = new_record.id
    db.add(old_record)
    db.flush()
    return raw_token, new_record


def revoke_user_refresh_tokens(db: Session, user_id, *, reason: str = "logout_all") -> int:
    now = datetime.now(timezone.utc)
    rows = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_active.is_(True),
            RefreshToken.revoked_at.is_(None),
        )
        .all()
    )
    for row in rows:
        row.is_active = False
        row.revoked_at = now
        row.revoked_reason = reason
        db.add(row)
    db.flush()
    return len(rows)
