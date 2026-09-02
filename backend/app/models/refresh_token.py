"""Refresh token model for persistent session lifecycle management."""
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship

from app.models import BaseModel


class RefreshToken(BaseModel):
    """Persisted refresh tokens with rotation and revocation metadata."""

    __tablename__ = "refresh_tokens"

    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked_at = Column(DateTime, nullable=True, index=True)
    revoked_reason = Column(String(64), nullable=True)
    rotated_to_token_id = Column(ForeignKey("refresh_tokens.id"), nullable=True, index=True)
    issued_ip = Column(String(64), nullable=True)
    issued_user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    user = relationship("User", backref="refresh_tokens", foreign_keys=[user_id])
    rotated_to = relationship("RefreshToken", remote_side="RefreshToken.id", uselist=False)

