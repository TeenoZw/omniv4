"""Authentication and authorization helpers for FastAPI routes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models import Hub
from app.models.hub_membership import HubMembership, HubMembershipStatus
from app.models.user import User, UserRole as DbUserRole

HUB_HEADER = "X-Hub-ID"


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


@dataclass
class HubAccessContext:
    """Represents the authenticated user's membership and subscription for a hub."""

    user: User
    hub: Optional[Hub]
    membership: Optional[HubMembership]


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _normalize_role(role: DbUserRole | str | None) -> str:
    if role is None:
        return ""
    if isinstance(role, DbUserRole):
        return role.value
    return str(role).lower()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from the bearer token."""

    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise _credentials_exception()

    try:
        user_id = UUID(str(payload["sub"]))
    except ValueError:
        raise _credentials_exception()

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise _credentials_exception()

    return user


def require_role(*allowed_roles: DbUserRole):
    """Return a dependency that ensures the user has one of the provided roles."""

    # Flatten args to a set of string role values
    role_values = {_normalize_role(role) for role in allowed_roles} if allowed_roles else set()

    def _dependency(user: User = Depends(get_current_user)) -> User:
        if role_values and _normalize_role(user.role) not in role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role to access this resource",
            )
        return user

    return _dependency


def _parse_hub_identifier(raw_value: str | None) -> UUID:
    if not raw_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing {HUB_HEADER} header",
        )
    try:
        return UUID(str(raw_value))
    except ValueError as exc:  # pragma: no cover - validated via FastAPI
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid hub identifier '{raw_value}'",
        ) from exc


def get_hub_context(
    hub_header: str = Header(None, alias=HUB_HEADER),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HubAccessContext:
    """Resolve the user's membership and subscription for a requested hub."""

    normalized_role = _normalize_role(user.role)
    allow_unscoped = normalized_role == DbUserRole.admin.value

    if not hub_header:
        if allow_unscoped:
            return HubAccessContext(
                user=user,
                hub=None,
                membership=None,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing {HUB_HEADER} header",
        )

    hub_id = _parse_hub_identifier(hub_header)
    hub = db.query(Hub).filter(Hub.id == hub_id).first()
    if not hub or hub.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hub not found",
        )

    membership = (
        db.query(HubMembership)
        .filter(
            HubMembership.hub_id == hub_id,
            HubMembership.user_id == user.id,
            HubMembership.status == HubMembershipStatus.active,
        )
        .first()
    )

    if not membership and not allow_unscoped:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of the requested hub",
        )

    return HubAccessContext(
        user=user,
        hub=hub,
        membership=membership,
    )


def require_hub_access(*allowed_roles: DbUserRole):
    """Ensure the caller belongs to the active hub with one of the provided roles."""

    role_values = {_normalize_role(role) for role in allowed_roles} if allowed_roles else set()

    def _dependency(context: HubAccessContext = Depends(get_hub_context)) -> HubAccessContext:
        if not role_values:
            return context

        membership_role = _normalize_role(context.membership.role if context.membership else context.user.role)
        if membership_role not in role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this hub",
            )
        return context

    return _dependency
