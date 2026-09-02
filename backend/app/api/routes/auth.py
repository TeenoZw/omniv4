"""Authentication helper routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, decode_token
from app.models.user import User
from app.services.admin_activity import append_admin_activity
from app.services.refresh_tokens import (
    get_valid_refresh_token,
    revoke_refresh_token,
    revoke_user_refresh_tokens,
    rotate_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str | None = None
    all_sessions: bool = False


bearer_optional = HTTPBearer(auto_error=False)


def _resolve_user_from_auth(
    credentials: HTTPAuthorizationCredentials | None,
    db: Session,
) -> User | None:
    if not credentials or not credentials.credentials:
        return None
    payload = decode_token(credentials.credentials)
    if not payload or "sub" not in payload:
        return None
    return db.query(User).filter(User.id == payload["sub"], User.is_active.is_(True)).first()


@router.post("/refresh")
async def refresh_token(
    payload: RefreshRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Rotate refresh token and issue a fresh access token."""
    existing = get_valid_refresh_token(db, payload.refresh_token)
    if not existing:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.query(User).filter(User.id == existing.user_id).first()
    if not user or not user.is_active:
        revoke_refresh_token(db, existing, reason="user_inactive")
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    new_refresh_token, _ = rotate_refresh_token(
        db,
        existing,
        user,
        issued_ip=request.client.host if request.client else None,
        issued_user_agent=request.headers.get("user-agent"),
    )
    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
    db.commit()

    append_admin_activity(
        db,
        module="auth",
        change="Token refreshed",
        details="Refresh token rotated and new access token issued",
        actor=user,
        target_type="session",
        target_id=str(user.id),
    )
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


@router.post("/logout")
async def logout(
    payload: LogoutRequest | None = None,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_optional),
    db: Session = Depends(get_db),
):
    """Revoke active refresh token(s) for the authenticated session/user."""
    payload = payload or LogoutRequest()
    revoked = 0
    user = _resolve_user_from_auth(credentials, db)

    if payload.refresh_token:
        token_record = get_valid_refresh_token(db, payload.refresh_token)
        if token_record:
            revoke_refresh_token(db, token_record, reason="logout")
            revoked += 1

    if user and payload.all_sessions:
        revoked += revoke_user_refresh_tokens(db, user.id, reason="logout_all")
    elif user and not payload.refresh_token:
        revoked += revoke_user_refresh_tokens(db, user.id, reason="logout")

    db.commit()
    if user:
        append_admin_activity(
            db,
            module="auth",
            change="User logout",
            details="Session revoked",
            actor=user,
            target_type="session",
            target_id=str(user.id),
        )
    return {"success": True, "revoked": revoked}
