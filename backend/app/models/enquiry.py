"""Enquiry model for customer onboarding and quotations."""
from __future__ import annotations

import enum
from sqlalchemy import JSON, Boolean, Column, DateTime, Enum as SQLEnum, Numeric, String, Text

from app.models import BaseModel


class EnquiryStatus(str, enum.Enum):
    """Lifecycle status for onboarding enquiries."""

    new = "new"
    quoted = "quoted"
    awaiting_payment = "awaiting_payment"
    onboarded = "onboarded"
    closed_lost = "closed_lost"


class CustomerType(str, enum.Enum):
    """Customer type classification."""

    individual = "individual"
    business = "business"


class Enquiry(BaseModel):
    """Tracks an onboarding enquiry submitted from the public landing page."""

    __tablename__ = "enquiries"

    status = Column(
        SQLEnum(EnquiryStatus, name="enquiry_status", native_enum=True),
        nullable=False,
        default=EnquiryStatus.new,
        index=True,
    )
    customer_type = Column(
        SQLEnum(CustomerType, name="enquiry_customer_type", native_enum=True),
        nullable=False,
        index=True,
    )
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(80), nullable=False)
    company_name = Column(String(255), nullable=True)
    fleet_size = Column(String(40), nullable=True)
    operating_area = Column(String(255), nullable=True)
    preferred_contact_method = Column(String(40), nullable=True)
    expected_go_live_date = Column(DateTime(timezone=True), nullable=True)
    tracking_use_case = Column(String(255), nullable=True)
    hardware_choices = Column(JSON, nullable=False, default=list)
    add_ons = Column(JSON, nullable=False, default=list)
    message = Column(Text, nullable=True)
    terms_accepted = Column(Boolean, nullable=False, default=False)
    privacy_accepted = Column(Boolean, nullable=False, default=False)

    quoted_monthly = Column(Numeric(10, 2), nullable=True)
    quoted_hardware_total = Column(Numeric(10, 2), nullable=True)
    quote_sent_at = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    admin_notes = Column(Text, nullable=True)
