"""Hub service helpers."""
from __future__ import annotations

from secrets import choice
import string
from typing import Optional

from sqlalchemy.orm import Session

from app.models.hub import Hub


def _clean(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _normalize_code(value: Optional[str]) -> Optional[str]:
    cleaned = _clean(value)
    if not cleaned:
        return None
    return cleaned.upper()


def _generate_code_from_name(name: Optional[str]) -> str:
    letters = "".join(ch for ch in (name or "") if ch.isalpha()).upper() or "HUB"
    prefix = (letters + "XXX")[:3]
    digits = "".join(choice(string.digits) for _ in range(4))
    return f"{prefix}-{digits}"


def _resolve_unique_code(
    db: Session,
    desired: Optional[str],
    *,
    allow_existing_id: Optional[str] = None,
    fallback_name: Optional[str] = None,
) -> str:
    """Return a hub code, preferring the desired value when globally unique; otherwise generate XXX-#### from name."""

    normalized = _normalize_code(desired)
    if normalized:
        existing = db.query(Hub).filter(Hub.code == normalized).one_or_none()
        if not existing or (allow_existing_id and str(existing.id) == str(allow_existing_id)):
            return normalized

    # Fallback deterministic-ish generator based on name prefix
    base_prefix = fallback_name or desired
    while True:
        candidate = _generate_code_from_name(base_prefix)
        existing = db.query(Hub).filter(Hub.code == candidate).first()
        if not existing:
            return candidate
        # ensure we eventually break collisions by appending a random hub code token
        base_prefix = None
