"""Device pairing workflow model."""
from __future__ import annotations

import enum
from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, Text, Uuid
from sqlalchemy.orm import relationship

from app.models import BaseModel


class PairingStatus(str, enum.Enum):
    """Pairing approval stages."""

    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class DevicePairing(BaseModel):
    """Tracks a device-to-vehicle pairing request."""

    __tablename__ = "device_pairings"

    hardware_id = Column(Integer, ForeignKey("hardware_inventory.id"), nullable=False)
    vehicle_id = Column(Uuid(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    requested_by = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_by = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(
        SQLEnum(PairingStatus, name="pairing_status", native_enum=True),
        nullable=False,
        default=PairingStatus.pending,
        index=True,
    )
    notes = Column(Text, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    hardware = relationship("HardwareInventory", back_populates="pairings")
    vehicle = relationship("Vehicle", back_populates="pairings")
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<DevicePairing hardware={self.hardware_id} vehicle={self.vehicle_id} status={self.status}>"
