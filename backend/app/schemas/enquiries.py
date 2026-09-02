"""Schemas for onboarding enquiries."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EnquiryBase(BaseModel):
    customer_type: str = Field(..., pattern="^(individual|business)$")
    full_name: str
    email: EmailStr
    phone: str
    company_name: Optional[str] = None
    fleet_size: Optional[str] = None
    operating_area: Optional[str] = None
    preferred_contact_method: Optional[str] = None
    expected_go_live_date: Optional[datetime] = None
    tracking_use_case: Optional[str] = None
    hardware_choices: List[str]
    add_ons: List[str] = []
    message: Optional[str] = None
    terms_accepted: bool
    privacy_accepted: bool


class EnquiryCreate(EnquiryBase):
    pass


class EnquiryUpdate(BaseModel):
    status: Optional[str] = Field(default=None, pattern="^(new|quoted|awaiting_payment|onboarded|closed_lost)$")
    quoted_monthly: Optional[float] = None
    quoted_hardware_total: Optional[float] = None
    quote_sent_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    admin_notes: Optional[str] = None


class EnquiryResponse(EnquiryBase):
    id: UUID
    status: str
    quoted_monthly: Optional[float] = None
    quoted_hardware_total: Optional[float] = None
    quote_sent_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
