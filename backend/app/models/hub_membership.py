"""Hub membership model linking users to hubs with per-hub roles."""
from __future__ import annotations

import enum
from sqlalchemy import Boolean, Column, Enum as SQLEnum, ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import relationship

from app.models import BaseModel
from app.models.user import UserRole


class HubMembershipStatus(str, enum.Enum):
    """Lifecycle status for hub memberships."""

    active = "active"
    invited = "invited"
    suspended = "suspended"


class HubMembership(BaseModel):
    """Assigns a user to a hub with a specific role."""

    __tablename__ = "hub_memberships"

    hub_id = Column(Uuid(as_uuid=True), ForeignKey("hubs.id"), nullable=False, index=True)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    role = Column(
        SQLEnum(
            UserRole,
            name="user_role",
            native_enum=True,
        ),
        nullable=False,
    )
    status = Column(
        SQLEnum(HubMembershipStatus, name="hub_membership_status", native_enum=True),
        nullable=False,
        default=HubMembershipStatus.active,
    )
    is_primary = Column(Boolean, nullable=False, default=False)

    hub = relationship("Hub", back_populates="memberships")
    user = relationship("User", back_populates="memberships")

    __table_args__ = (
        UniqueConstraint("hub_id", "user_id", name="uq_hub_membership_user"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<HubMembership hub={self.hub_id} user={self.user_id} role={self.role}>"
