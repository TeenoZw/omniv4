"""Technician workflow job card model."""
from __future__ import annotations

import enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import relationship

from app.models import BaseModel


class TechnicianJobStatus(str, enum.Enum):
    """Lifecycle states for technician job cards."""

    pending = "pending"
    assigned = "assigned"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class TechnicianJobPriority(str, enum.Enum):
    """Priority levels for installation work."""

    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


class TechnicianJob(BaseModel):
    """Tracks installation work from assignment to completion."""

    __tablename__ = "technician_jobs"

    hub_id = Column(Uuid(as_uuid=True), ForeignKey("hubs.id"), nullable=False, index=True)
    hardware_id = Column(Integer, ForeignKey("hardware_inventory.id"), nullable=True, index=True)
    vehicle_id = Column(Uuid(as_uuid=True), ForeignKey("vehicles.id"), nullable=True, index=True)
    requested_by = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    assigned_technician_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    status = Column(
        SQLEnum(
            TechnicianJobStatus,
            name="technician_job_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            native_enum=True,
            validate_strings=True,
            create_constraint=False,
        ),
        nullable=False,
        default=TechnicianJobStatus.pending,
        index=True,
    )
    priority = Column(
        SQLEnum(
            TechnicianJobPriority,
            name="technician_job_priority",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            native_enum=True,
            validate_strings=True,
            create_constraint=False,
        ),
        nullable=False,
        default=TechnicianJobPriority.normal,
        index=True,
    )
    scheduled_for = Column(DateTime(timezone=True), nullable=True, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    declined_at = Column(DateTime(timezone=True), nullable=True)
    installed_at = Column(DateTime(timezone=True), nullable=True)
    installation_location = Column(String(255), nullable=True)
    installation_latitude = Column(Numeric(10, 7), nullable=True)
    installation_longitude = Column(Numeric(10, 7), nullable=True)
    asset_label = Column(String(255), nullable=True)
    asset_registration = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    completion_notes = Column(Text, nullable=True)
    decline_reason = Column(Text, nullable=True)
    assignment_reference = Column(String(64), nullable=True)

    hub = relationship("Hub", foreign_keys=[hub_id])
    hardware = relationship("HardwareInventory", foreign_keys=[hardware_id])
    vehicle = relationship("Vehicle", foreign_keys=[vehicle_id])
    requester = relationship("User", foreign_keys=[requested_by])
    assigned_technician = relationship("User", foreign_keys=[assigned_technician_id])

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<TechnicianJob {self.id} status={self.status}>"
