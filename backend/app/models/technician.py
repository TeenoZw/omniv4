"""Technician model."""
from sqlalchemy import Column, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from app.models import BaseModel


class Technician(BaseModel):
    """Technician model."""

    __tablename__ = "technicians"

    user_id = Column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    hub_id = Column(
        Uuid(as_uuid=True), ForeignKey("hubs.id"), nullable=False, index=True
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    hub = relationship("Hub", back_populates="technicians")

    def __repr__(self) -> str:
        return f"<Technician {self.user_id}>"
