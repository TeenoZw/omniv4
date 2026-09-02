"""Asset model stored in the legacy vehicles table."""
from sqlalchemy import Column, Enum as SQLEnum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import relationship
import enum
from app.models import BaseModel


class VehicleStatus(str, enum.Enum):
    """Asset status."""

    active = "active"
    inactive = "inactive"
    maintenance = "maintenance"
    retired = "retired"


class Vehicle(BaseModel):
    """Asset model.

    The table name remains ``vehicles`` for compatibility, but records now
    represent any trackable customer asset created during onboarding.
    """

    __tablename__ = "vehicles"

    imei = Column(String(20), unique=True, nullable=True, index=True)
    license_plate = Column(String(20), unique=True, nullable=True, index=True)
    vin = Column(String(64), unique=True, nullable=True, index=True)
    asset_type = Column(String(50), nullable=False, default="vehicle", server_default="vehicle")
    asset_name = Column(String(255), nullable=False, default="Unnamed asset", server_default="Unnamed asset")
    asset_type_other = Column(String(100), nullable=True)
    make = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    year = Column(String(4), nullable=True)
    color = Column(String(50), nullable=True)
    engine_capacity = Column(String(50), nullable=True)
    co2_emissions = Column(String(50), nullable=True)
    fuel_type = Column(String(50), nullable=True)
    photo_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    source_job_id = Column(
        Uuid(as_uuid=True), ForeignKey("technician_jobs.id"), nullable=True, index=True
    )
    status = Column(
        SQLEnum(
            VehicleStatus,
            name="vehicle_status",
            native_enum=True,
        ),
        default=VehicleStatus.active,
        nullable=False,
    )
    hub_id = Column(
        Uuid(as_uuid=True), ForeignKey("hubs.id"), nullable=False, index=True
    )

    # Relationships
    hub = relationship("Hub", back_populates="vehicles")
    devices = relationship("Device", back_populates="vehicle")
    source_job = relationship("TechnicianJob", foreign_keys=[source_job_id])
    pairings = relationship(
        "DevicePairing",
        back_populates="vehicle",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Vehicle {self.asset_name or self.license_plate or self.id}>"
