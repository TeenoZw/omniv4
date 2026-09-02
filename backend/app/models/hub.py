"""Hub model."""
from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import relationship
from app.models import BaseModel


class Hub(BaseModel):
    """Hub model."""

    __tablename__ = "hubs"

    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False, unique=True, index=True)
    location = Column(String(255), nullable=True)
    timezone = Column(String(64), nullable=True)
    hub_type = Column(String(50), nullable=True)
    subscription_tier = Column(String(50), nullable=True)
    payment_method = Column(String(50), nullable=True)
    billing_cycle = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True)
    country = Column(String(120), nullable=True)
    city = Column(String(120), nullable=True)
    address_line = Column(String(255), nullable=True)
    currency = Column(String(10), nullable=True)
    go_live_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    primary_contact_name = Column(String(255), nullable=True)
    primary_contact_email = Column(String(255), nullable=True)
    primary_contact_phone = Column(String(50), nullable=True)
    billing_contact_name = Column(String(255), nullable=True)
    billing_contact_email = Column(String(255), nullable=True)
    billing_contact_phone = Column(String(50), nullable=True)
    device_count = Column(Integer, nullable=False, default=0)
    vehicle_count = Column(Integer, nullable=False, default=0)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    owner_id = Column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    description = Column(String(500), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    recycle_bin_expires_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Relationships
    owner = relationship("User", back_populates="hubs")
    vehicles = relationship("Vehicle", back_populates="hub")
    technicians = relationship("Technician", back_populates="hub")
    memberships = relationship(
        "HubMembership",
        back_populates="hub",
        cascade="all, delete-orphan",
    )
    subscriptions = relationship(
        "Subscription",
        back_populates="hub",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Hub {self.name}>"
