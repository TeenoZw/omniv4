"""Subscription model."""
from sqlalchemy import Boolean, Column, Date, ForeignKey, String, Uuid
from sqlalchemy.orm import relationship

from app.models import BaseModel


class Subscription(BaseModel):
    """Subscription model."""

    __tablename__ = "subscriptions"

    user_id = Column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    hub_id = Column(
        Uuid(as_uuid=True), ForeignKey("hubs.id"), nullable=True, index=True
    )
    tier = Column(String(50), default="individual", nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    auto_renew = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User")
    hub = relationship("Hub", back_populates="subscriptions")

    def __repr__(self) -> str:
        return f"<Subscription hub={self.hub_id} ({self.tier})>"
