"""Base model for all SQLAlchemy models."""
from sqlalchemy import Column, DateTime, Uuid, func
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()


class BaseModel(Base):
    """Base model for all database models."""

    __abstract__ = True

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


# Import all models
from app.models.user import User  # noqa: E402, F401
from app.models.hub import Hub  # noqa: E402, F401
from app.models.vehicle import Vehicle  # noqa: E402, F401
from app.models.device import Device  # noqa: E402, F401
from app.models.subscription import Subscription  # noqa: E402, F401
from app.models.technician import Technician  # noqa: E402, F401
from app.models.hardware import (  # noqa: E402, F401
    HardwareInventory,
    HardwareAssignment,
    HardwareStatus,
    SimInventory,
    SimAssignment,
    SimStatus,
)
from app.models.pairing import DevicePairing, PairingStatus  # noqa: E402, F401
from app.models.hub_membership import HubMembership, HubMembershipStatus  # noqa: E402, F401
from app.models.enquiry import Enquiry, EnquiryStatus, CustomerType  # noqa: E402, F401
from app.models.admin_activity import AdminActivityLog  # noqa: E402, F401
from app.models.refresh_token import RefreshToken  # noqa: E402, F401
from app.models.technician_job import (  # noqa: E402, F401
    TechnicianJob,
    TechnicianJobStatus,
    TechnicianJobPriority,
)
from app.models.compliance import (  # noqa: E402, F401
    ComplianceAttachment,
    DataSubjectRequest,
    SecurityIncident,
)
from app.models.v4_foundation import (  # noqa: E402, F401
    Account,
    BusinessDocument,
    BusinessDocumentLine,
    Company,
    DocumentSequence,
    FiscalPeriod,
    Item,
    JournalEntry,
    JournalLine,
    Party,
    StockMovement,
    Warehouse,
)
