"""Device model."""
from sqlalchemy import Column, Enum as SQLEnum, ForeignKey, String, Uuid
from sqlalchemy.orm import relationship
import enum
from app.models import BaseModel


class DeviceStatus(str, enum.Enum):
    """Device status."""

    active = "active"
    inactive = "inactive"
    faulty = "faulty"
    unassigned = "unassigned"


class Device(BaseModel):
    """Device model."""

    __tablename__ = "devices"

    imei = Column(String(20), unique=True, nullable=False, index=True)
    model = Column(String(100), nullable=False)
    firmware_version = Column(String(50), nullable=True)
    status = Column(
        SQLEnum(
            DeviceStatus,
            name="device_status",
            native_enum=True,
        ),
        default=DeviceStatus.unassigned,
        nullable=False,
    )
    vehicle_id = Column(
        Uuid(as_uuid=True), ForeignKey("vehicles.id"), nullable=True, index=True
    )
    assigned_to = Column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )

    # Relationships
    vehicle = relationship("Vehicle", back_populates="devices")
    user = relationship("User", foreign_keys=[assigned_to])

    def __repr__(self) -> str:
        return f"<Device {self.imei}>"
