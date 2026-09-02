"""Pydantic schemas for hub provisioning APIs."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class HubContact(BaseModel):
    """Contact details for a hub."""

    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class HubUserCreate(BaseModel):
    """Payload to create and invite a hub operator."""

    name: str = Field(..., min_length=1)
    email: EmailStr
    role: str = Field("viewer", description="Role label requested by the UI")
    password: Optional[str] = Field(
        default=None,
        min_length=8,
        description="Required when creating a brand-new user account",
    )


class HubUserUpdate(BaseModel):
    """Payload to edit an existing hub user account."""

    name: Optional[str] = Field(default=None, min_length=1)
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(default=None, description="Role label requested by the UI")
    password: Optional[str] = Field(
        default=None,
        min_length=8,
        description="Optional password reset (minimum 8 characters)",
    )


class HubCreate(BaseModel):
    """Payload for provisioning a hub."""

    hub_name: str = Field(..., alias="name", min_length=1)
    hub_code: Optional[str] = Field(None, alias="code")
    hub_type: Optional[str] = Field("company", alias="type")
    subscription_tier: Optional[str] = Field("individual", alias="tier")
    payment_method: Optional[str] = "manual_invoice"
    billing_cycle: Optional[str] = "monthly"
    timezone: Optional[str] = "UTC"
    country: Optional[str] = None
    city: Optional[str] = None
    address_line: Optional[str] = None
    currency: Optional[str] = Field(None, max_length=10)
    go_live_date: Optional[str] = None
    notes: Optional[str] = None
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[EmailStr] = None
    primary_contact_phone: Optional[str] = None
    billing_contact_name: Optional[str] = None
    billing_contact_email: Optional[EmailStr] = None
    billing_contact_phone: Optional[str] = None
    users: List[HubUserCreate] = Field(default_factory=list)


class HubUpdate(BaseModel):
    """Patch payload for existing hubs."""

    hub_name: Optional[str] = Field(None, alias="name")
    hub_type: Optional[str] = Field(None, alias="type")
    subscription_tier: Optional[str] = Field(None, alias="tier")
    payment_method: Optional[str] = None
    billing_cycle: Optional[str] = None
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[EmailStr] = None
    primary_contact_phone: Optional[str] = None
    billing_contact_name: Optional[str] = None
    billing_contact_email: Optional[EmailStr] = None
    timezone: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    address_line: Optional[str] = None
    currency: Optional[str] = Field(None, max_length=10)
    go_live_date: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    billing_contact_phone: Optional[str] = None
    days_left: Optional[int] = Field(None, ge=0)
    subscription_start_date: Optional[str] = None
    subscription_end_date: Optional[str] = None


class HubResponse(BaseModel):
    """API response model for hubs."""

    id: str
    name: str
    code: str
    type: str
    tier: str
    payment_method: str
    billing_cycle: str
    status: str
    timezone: str | None = None
    country: str | None = None
    city: str | None = None
    address: str | None = None
    go_live_date: str | None = None
    notes: str | None = None
    currency: str | None = None
    billing_contact_phone: str | None = None
    subscription_days_left: int | None = None
    subscription_start_date: str | None = None
    subscription_end_date: str | None = None
    device_count: int = 0
    vehicle_count: int = 0
    primary_contact: HubContact
    billing_contact: HubContact
    users: list[dict] = Field(default_factory=list)
    devices: list[dict] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class HubAssetDeviceResponse(BaseModel):
    """Active hardware assignment attached to a hub asset."""

    assignment_id: int | None = None
    hardware_id: int | None = None
    imei: str
    serial_number: str | None = None
    model: str | None = None
    hardware_type: str | None = None
    manufacturer: str | None = None
    firmware_version: str | None = None
    status: str | None = None
    asset_label: str | None = None
    asset_registration: str | None = None
    installation_location: str | None = None
    technician: str | None = None
    assigned_at: datetime | None = None
    installed_at: datetime | None = None
    vehicle_id: str | None = None
    vehicle_label: str | None = None
    assignment_history: list["HubAssetAssignmentHistoryItem"] = Field(default_factory=list)


class HubAssetAssignmentHistoryItem(BaseModel):
    """Historical assignment entry for a hardware unit exposed from the hub asset view."""

    id: int
    target: str | None = None
    hub_id: str | None = None
    hub_name: str | None = None
    vehicle_id: str | None = None
    vehicle_label: str | None = None
    technician: str | None = None
    assigned_at: datetime | None = None
    installed_at: datetime | None = None
    unassigned_at: datetime | None = None
    installation_location: str | None = None
    installation_latitude: float | None = None
    installation_longitude: float | None = None
    asset_label: str | None = None
    asset_registration: str | None = None
    notes: str | None = None
    is_active: bool = False


class HubAssetResponse(BaseModel):
    """Asset summary within a hub."""

    id: str
    asset_type: str | None = None
    asset_name: str | None = None
    asset_type_other: str | None = None
    registration: str | None = None
    label: str | None = None
    vin: str | None = None
    make: str | None = None
    model: str | None = None
    year: str | None = None
    color: str | None = None
    engine_capacity: str | None = None
    co2_emissions: str | None = None
    fuel_type: str | None = None
    status: str | None = None
    notes: str | None = None
    tracking_state: str | None = None
    source_job_id: str | None = None
    assigned_device_count: int = 0
    last_assignment_at: datetime | None = None


class HubAssetDetailResponse(HubAssetResponse):
    """Asset detail plus currently assigned devices."""

    hub_id: str
    hub_code: str
    hub_name: str
    devices: list[HubAssetDeviceResponse] = Field(default_factory=list)


class HubAssetListData(BaseModel):
    """Container for asset list responses."""

    items: list[HubAssetResponse] = Field(default_factory=list)


class HubAssetPaginationMeta(BaseModel):
    """Pagination metadata for hub asset list responses."""

    page: int
    per_page: int
    total: int


class HubAssetListResponse(BaseModel):
    """Paginated hub asset list payload."""

    data: HubAssetListData
    meta: HubAssetPaginationMeta


class HubBulkDeleteRequest(BaseModel):
    """Payload for deleting multiple hubs."""

    hub_ids: list[str] = Field(default_factory=list, min_length=1)


class HubAssetHardwareAssignment(BaseModel):
    """Hardware and SIM pairing payload for a hub asset capture."""

    hardware_id: int
    sim_id: Optional[int] = None


class HubAssetCreate(BaseModel):
    """Payload for creating a new hub asset."""

    asset_type: str = Field(..., min_length=1)
    asset_name: str = Field(..., min_length=1)
    asset_type_other: Optional[str] = Field(default=None, max_length=100)
    registration: Optional[str] = Field(default=None, max_length=20)
    vin: Optional[str] = Field(default=None, max_length=64)
    make: Optional[str] = Field(default=None, max_length=100)
    model: Optional[str] = Field(default=None, max_length=100)
    year: Optional[str] = Field(default=None, max_length=4)
    color: Optional[str] = Field(default=None, max_length=50)
    engine_capacity: Optional[str] = Field(default=None, max_length=50)
    co2_emissions: Optional[str] = Field(default=None, max_length=50)
    fuel_type: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = None
    source_job_id: Optional[str] = None
    hardware_ids: list[int] = Field(default_factory=list)
    hardware_assignments: list[HubAssetHardwareAssignment] = Field(default_factory=list)


class HubAssetUpdate(BaseModel):
    """Payload for updating an existing hub asset."""

    asset_type: Optional[str] = Field(default=None, min_length=1)
    asset_name: Optional[str] = Field(default=None, min_length=1)
    asset_type_other: Optional[str] = Field(default=None, max_length=100)
    registration: Optional[str] = Field(default=None, max_length=20)
    vin: Optional[str] = Field(default=None, max_length=64)
    make: Optional[str] = Field(default=None, max_length=100)
    model: Optional[str] = Field(default=None, max_length=100)
    year: Optional[str] = Field(default=None, max_length=4)
    color: Optional[str] = Field(default=None, max_length=50)
    engine_capacity: Optional[str] = Field(default=None, max_length=50)
    co2_emissions: Optional[str] = Field(default=None, max_length=50)
    fuel_type: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = None


class VinDecodeRequest(BaseModel):
    """Request payload for VIN decoding."""

    vin: str = Field(..., min_length=17, max_length=32)


class VinDecodeData(BaseModel):
    """Decoded VIN metadata."""

    vin: str
    normalized_vin: str
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[str] = None
    vehicle_type: Optional[str] = None
    body_class: Optional[str] = None
    fuel_type: Optional[str] = None
    engine_capacity: Optional[str] = None
    suggested_asset_type: Optional[str] = None
    manufacturer: Optional[str] = None


class VinDecodeResponse(BaseModel):
    """VIN decoding response payload."""

    success: bool
    provider: str
    warnings: list[str] = Field(default_factory=list)
    decoded: VinDecodeData
