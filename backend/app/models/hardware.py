"""Hardware inventory and assignment models."""
from __future__ import annotations

import enum
from sqlalchemy import (
    Boolean,
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
from sqlalchemy.sql import func

from app.models import Base


class HardwareStatus(str, enum.Enum):
    """Operational states for hardware devices."""

    IN_STOCK = "in_stock"
    ASSIGNED = "assigned"
    ACTIVE = "active"
    FAULTY = "faulty"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class SimStatus(str, enum.Enum):
    """Operational states for SIM inventory."""

    IN_STOCK = "in_stock"
    ASSIGNED = "assigned"
    SUSPENDED = "suspended"
    FAULTY = "faulty"
    RETIRED = "retired"


class HardwareInventory(Base):
    """Represents a physical tracking device in inventory."""

    __tablename__ = "hardware_inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    imei = Column(String(32), unique=True, nullable=False, index=True)
    serial_number = Column(String(64), unique=True, nullable=True)
    hardware_type = Column(String(64), nullable=True)
    model = Column(String(100), nullable=True)
    manufacturer = Column(String(100), nullable=True)
    firmware_version = Column(String(64), nullable=True)
    iccid = Column(String(32), unique=True, nullable=True)
    purchase_date = Column(DateTime(timezone=True), nullable=True)
    purchase_cost = Column(Numeric(12, 2), nullable=True)
    status = Column(
        SQLEnum(
            HardwareStatus,
            name="hardwarestatus",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            native_enum=True,
            validate_strings=True,
            create_constraint=False,
        ),
        nullable=False,
        default=HardwareStatus.IN_STOCK,
        index=True,
    )
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    assignments = relationship(
        "HardwareAssignment",
        back_populates="hardware",
        cascade="all, delete-orphan",
    )
    pairings = relationship(
        "DevicePairing",
        back_populates="hardware",
        cascade="all, delete-orphan",
    )
    sim_assignments = relationship(
        "SimAssignment",
        back_populates="hardware",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<HardwareInventory imei={self.imei} status={self.status}>"


class HardwareAssignment(Base):
    """Tracks hardware-to-hub/vehicle assignments over time."""

    __tablename__ = "hardware_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    hardware_id = Column(Integer, ForeignKey("hardware_inventory.id"), nullable=False)
    hub_id = Column(Uuid(as_uuid=True), ForeignKey("hubs.id"), nullable=True)
    vehicle_id = Column(Uuid(as_uuid=True), ForeignKey("vehicles.id"), nullable=True)
    assigned_by = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    installed_at = Column(DateTime(timezone=True), nullable=True)
    installation_location = Column(String(255), nullable=True)
    installation_latitude = Column(Numeric(10, 7), nullable=True)
    installation_longitude = Column(Numeric(10, 7), nullable=True)
    asset_label = Column(String(255), nullable=True)
    asset_registration = Column(String(100), nullable=True)
    unassigned_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    hardware = relationship("HardwareInventory", back_populates="assignments")
    vehicle = relationship("Vehicle")
    hub = relationship("Hub")
    assigned_user = relationship("User")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<HardwareAssignment hardware_id={self.hardware_id} active={self.is_active}>"


class SimInventory(Base):
    """Represents a physical SIM card managed alongside trackers."""

    __tablename__ = "sim_inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    iccid = Column(String(32), unique=True, nullable=False, index=True)
    msisdn = Column(String(32), unique=True, nullable=True, index=True)
    carrier = Column(String(100), nullable=False, default="Econet", server_default="Econet")
    apn = Column(String(128), nullable=True)
    roaming_enabled = Column(Boolean, nullable=False, default=False, server_default="false")
    roaming_regions = Column(Text, nullable=True)
    status = Column(
        SQLEnum(
            SimStatus,
            name="simstatus",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            native_enum=True,
            validate_strings=True,
            create_constraint=False,
        ),
        nullable=False,
        default=SimStatus.IN_STOCK,
        index=True,
    )
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    assignments = relationship(
        "SimAssignment",
        back_populates="sim",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<SimInventory iccid={self.iccid} status={self.status}>"


class SimAssignment(Base):
    """Tracks SIM-to-tracker assignments over time."""

    __tablename__ = "sim_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sim_id = Column(Integer, ForeignKey("sim_inventory.id"), nullable=False, index=True)
    hardware_id = Column(Integer, ForeignKey("hardware_inventory.id"), nullable=False, index=True)
    hub_id = Column(Uuid(as_uuid=True), ForeignKey("hubs.id"), nullable=True)
    vehicle_id = Column(Uuid(as_uuid=True), ForeignKey("vehicles.id"), nullable=True)
    assigned_by = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    unassigned_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    sim = relationship("SimInventory", back_populates="assignments")
    hardware = relationship("HardwareInventory", back_populates="sim_assignments")
    vehicle = relationship("Vehicle")
    hub = relationship("Hub")
    assigned_user = relationship("User")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<SimAssignment sim_id={self.sim_id} hardware_id={self.hardware_id} active={self.is_active}>"
