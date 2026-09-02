"""User routes."""
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

import logging

from app.core.auth import get_current_user, require_role
from app.core.database import get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
)
from app.core.config import settings
from app.models.hub import Hub
from app.models.hub_membership import HubMembership, HubMembershipStatus
from app.models.user import User, UserRole as DbUserRole
from app.schemas import UserCreate, UserResponse, UserUpdate, TokenResponse, LoginRequest
from app.services.admin_activity import append_admin_activity
from app.services.refresh_tokens import issue_refresh_token

logger = logging.getLogger(__name__)
router = APIRouter()

ADMIN_ONLY = (DbUserRole.admin,)
LOGIN_WINDOW_MINUTES = 15
MAX_FAILED_LOGIN_ATTEMPTS = 10
FAILED_LOGIN_ATTEMPTS: dict[str, deque[datetime]] = defaultdict(deque)
FAILED_LOGIN_LOCK = Lock()


def _is_admin(user: User) -> bool:
    role_value = user.role.value if isinstance(user.role, DbUserRole) else str(user.role)
    return role_value == DbUserRole.admin.value


def _is_internal_operator(user: User) -> bool:
    role_value = user.role.value if isinstance(user.role, DbUserRole) else str(user.role)
    normalized = (role_value or "").strip().lower()
    return normalized in {DbUserRole.admin.value, DbUserRole.technician.value}


def _normalize_email(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _is_bootstrap_admin(user: User | None) -> bool:
    if user is None:
        return False
    return _normalize_email(user.email) == _normalize_email(settings.bootstrap_admin_email)


def _ensure_mutable_user(target_user: User) -> None:
    if _is_bootstrap_admin(target_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The superuser account cannot be changed or removed from the admin console.",
        )


def _normalize_hub_code(code: Optional[str]) -> Optional[str]:
    if code is None:
        return None
    cleaned = code.strip()
    if not cleaned:
        return None
    return cleaned.upper()


def _serialize_hub(hub: Hub, role: str) -> dict:
    return {
        "id": hub.id,
        "code": hub.code,
        "name": hub.name,
        "role": role,
        "subscription_tier": hub.subscription_tier,
        "status": hub.status,
    }


def _is_deleted_hub(hub: Hub | None) -> bool:
    return bool(hub and hub.deleted_at is not None)


def _client_identity(request: Request, email: str) -> str:
    ip = request.client.host if request.client and request.client.host else "unknown"
    return f"{ip}:{email.strip().lower()}"


def _prune_attempts(identity: str, now: datetime) -> None:
    attempts = FAILED_LOGIN_ATTEMPTS.get(identity)
    if not attempts:
        return
    cutoff = now - timedelta(minutes=LOGIN_WINDOW_MINUTES)
    while attempts and attempts[0] < cutoff:
        attempts.popleft()
    if not attempts:
        FAILED_LOGIN_ATTEMPTS.pop(identity, None)


def _enforce_login_rate_limit(identity: str) -> None:
    now = datetime.now(timezone.utc)
    with FAILED_LOGIN_LOCK:
        _prune_attempts(identity, now)
        attempts = FAILED_LOGIN_ATTEMPTS.get(identity)
        if attempts and len(attempts) >= MAX_FAILED_LOGIN_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Try again later.",
            )


def _record_failed_login(identity: str) -> None:
    now = datetime.now(timezone.utc)
    with FAILED_LOGIN_LOCK:
        _prune_attempts(identity, now)
        FAILED_LOGIN_ATTEMPTS[identity].append(now)


def _clear_failed_logins(identity: str) -> None:
    with FAILED_LOGIN_LOCK:
        FAILED_LOGIN_ATTEMPTS.pop(identity, None)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user: UserCreate,
    _: User = Depends(require_role(*ADMIN_ONLY)),
    db: Session = Depends(get_db),
):
    """Register a new user."""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    db_user = User(
        name=user.name,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        hashed_password=get_password_hash(user.password),
        role=user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    append_admin_activity(
        db,
        module="users",
        change="System user created",
        details=f"{db_user.email} created as {db_user.role.value}",
        actor=_,
        target_type="user",
        target_id=str(db_user.id),
    )
    return db_user


@router.get("/technicians")
async def list_technicians(
    _: User = Depends(require_role(*ADMIN_ONLY)),
    db: Session = Depends(get_db),
):
    """List all active technician accounts in the system."""
    technicians = (
        db.query(User)
        .filter(
            User.role == DbUserRole.technician,
            User.is_active.is_(True),
        )
        .order_by(User.name.asc(), User.email.asc())
        .all()
    )
    return [
        {
            "id": str(technician.id),
            "name": technician.name,
            "email": technician.email,
            "role": technician.role.value if hasattr(technician.role, "value") else str(technician.role),
        }
        for technician in technicians
    ]


@router.get("", response_model=list[UserResponse])
async def list_users(
    _: User = Depends(require_role(*ADMIN_ONLY)),
    db: Session = Depends(get_db),
):
    """List all active system users."""
    return (
        db.query(User)
        .filter(User.is_active.is_(True))
        .order_by(User.name.asc(), User.email.asc())
        .all()
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Login user."""
    identity = _client_identity(request, credentials.email)
    _enforce_login_rate_limit(identity)

    user = db.query(User).filter(User.email == credentials.email).first()
    password_valid = bool(user) and verify_password(credentials.password, user.hashed_password)
    if not user or not password_valid:
        _record_failed_login(identity)
        logger.warning(
            "Login failed for email %s (exists=%s, password_valid=%s)",
            credentials.email,
            bool(user),
            password_valid,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    _clear_failed_logins(identity)

    hub = None
    normalized_code = _normalize_hub_code(credentials.hub_code)
    is_internal = _is_internal_operator(user)

    if not is_internal:
        if normalized_code:
            hub = db.query(Hub).filter(Hub.code == normalized_code).first()
            if not hub:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Hub not found",
                )
            if _is_deleted_hub(hub):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Hub is in recycle bin",
                )
            membership = (
                db.query(HubMembership)
                .filter(
                    HubMembership.hub_id == hub.id,
                    HubMembership.user_id == user.id,
                    HubMembership.status == HubMembershipStatus.active,
                )
                .first()
            )
            if not membership:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User is not a member of the specified hub",
                )
        else:
            memberships = (
                db.query(HubMembership)
                .join(Hub, Hub.id == HubMembership.hub_id)
                .filter(
                    HubMembership.user_id == user.id,
                    HubMembership.status == HubMembershipStatus.active,
                    Hub.deleted_at.is_(None),
                )
                .order_by(Hub.name.asc())
                .all()
            )
            if len(memberships) == 0:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User is not assigned to any active hub",
                )
            if len(memberships) > 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Hub code is required when the user belongs to multiple hubs",
                )
            membership = memberships[0]
            hub = membership.hub
    elif normalized_code:
        hub = db.query(Hub).filter(Hub.code == normalized_code).first()
        if not hub:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hub not found",
            )
        if _is_deleted_hub(hub):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hub is in recycle bin",
            )

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    refresh_token, _ = issue_refresh_token(
        db,
        user,
        issued_ip=request.client.host if request.client else None,
        issued_user_agent=request.headers.get("user-agent"),
    )
    db.commit()

    hub_payload: list[dict] = []
    if _is_internal_operator(user):
        admin_hubs = db.query(Hub).filter(Hub.deleted_at.is_(None)).order_by(Hub.name.asc()).all()
        role_label = "admin" if _is_admin(user) else "technician"
        hub_payload = [_serialize_hub(item, role_label) for item in admin_hubs]
    else:
        memberships = (
            db.query(HubMembership)
            .join(Hub, Hub.id == HubMembership.hub_id)
            .filter(
                HubMembership.user_id == user.id,
                HubMembership.status == HubMembershipStatus.active,
                Hub.deleted_at.is_(None),
            )
            .order_by(Hub.name.asc())
            .all()
        )
        hub_payload = [
            _serialize_hub(
                membership.hub,
                membership.role.value if hasattr(membership.role, "value") else str(membership.role),
            )
            for membership in memberships
            if membership.hub is not None
        ]
        if hub is None and memberships:
            hub = memberships[0].hub

    response_payload = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": settings.access_token_expire_minutes * 60,
        "user_id": user.id,
        "user_name": user.name,
        "roles": [user.role.value if hasattr(user.role, "value") else str(user.role)],
        "hubs": hub_payload,
        "current_hub_id": hub.id if hub else None,
        "hub_id": hub.id if hub else None,
        "hub_code": hub.code if hub else None,
        "hub_name": hub.name if hub else None,
    }
    append_admin_activity(
        db,
        module="auth",
        change="User login",
        details=f"Authenticated into {hub.code if hub else 'admin scope'}",
        actor=user,
        target_type="hub" if hub else "session",
        target_id=str(hub.id) if hub else str(user.id),
    )
    return response_payload


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if not _is_admin(current_user) and str(current_user.id) != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view this user",
        )
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    actor: User = Depends(require_role(*ADMIN_ONLY)),
    db: Session = Depends(get_db),
):
    """Update an internal system user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    _ensure_mutable_user(user)

    changed_fields: list[str] = []

    if payload.name is not None:
        next_name = payload.name.strip()
        if next_name and next_name != user.name:
            changed_fields.append(f"name:{user.name}->{next_name}")
            user.name = next_name

    if payload.first_name is not None:
        next_first_name = payload.first_name.strip() or None
        if next_first_name != user.first_name:
            changed_fields.append("first_name")
            user.first_name = next_first_name

    if payload.last_name is not None:
        next_last_name = payload.last_name.strip() or None
        if next_last_name != user.last_name:
            changed_fields.append("last_name")
            user.last_name = next_last_name

    if payload.email is not None:
        email_value = _normalize_email(payload.email)
        if not email_value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required")
        if email_value != _normalize_email(user.email):
            email_exists = (
                db.query(User)
                .filter(func.lower(User.email) == email_value, User.id != user.id)
                .first()
            )
            if email_exists:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already in use")
            changed_fields.append(f"email:{user.email}->{email_value}")
            user.email = email_value

    if payload.role is not None and payload.role != user.role:
        changed_fields.append(f"role:{user.role.value}->{payload.role.value}")
        user.role = DbUserRole(payload.role.value)

    if payload.password:
        if len(payload.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least 8 characters",
            )
        user.hashed_password = get_password_hash(payload.password)
        user.is_active = True
        changed_fields.append("password:reset")

    if payload.is_active is not None and payload.is_active != user.is_active:
        if str(actor.id) == str(user.id) and not payload.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot deactivate your own account.",
            )
        changed_fields.append(f"is_active:{user.is_active}->{payload.is_active}")
        user.is_active = payload.is_active

    if not changed_fields:
        return user

    db.add(user)
    db.commit()
    db.refresh(user)
    append_admin_activity(
        db,
        module="users",
        change="System user updated",
        details=f"{user.email} updated [{', '.join(changed_fields)}]",
        actor=actor,
        target_type="user",
        target_id=str(user.id),
    )
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    actor: User = Depends(require_role(*ADMIN_ONLY)),
    db: Session = Depends(get_db),
):
    """Soft-delete a system user by deactivating the account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    _ensure_mutable_user(user)

    if str(actor.id) == str(user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account.",
        )

    if not user.is_active:
        return None

    user.is_active = False
    db.add(user)
    db.commit()
    append_admin_activity(
        db,
        module="users",
        change="System user deactivated",
        details=f"{user.email} deactivated",
        actor=actor,
        target_type="user",
        target_id=str(user.id),
    )
    return None
