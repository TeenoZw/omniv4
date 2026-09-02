"""Device inventory schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.hardware import HardwareStatus, SimStatus


class DeviceAssignment(BaseModel):
    """Current hardware assignment details."""

    target: str
    hub_id: Optional[UUID]
    hub_name: Optional[str]
    vehicle_id: Optional[UUID]
    vehicle_label: Optional[str]
    technician: Optional[str]
    assigned_at: Optional[datetime]
    installed_at: Optional[datetime]
    installation_location: Optional[str]
    installation_latitude: Optional[float]
    installation_longitude: Optional[float]
    asset_label: Optional[str]
    asset_registration: Optional[str]
    notes: Optional[str]
    sim_id: Optional[int] = None
    sim_iccid: Optional[str] = None
    sim_msisdn: Optional[str] = None
    sim_carrier: Optional[str] = None
    sim_roaming_enabled: Optional[bool] = None


class DeviceAssignmentHistoryItem(BaseModel):
    """Historical hardware assignment entry."""

    id: int
    target: str
    hub_id: Optional[UUID]
    hub_name: Optional[str]
    vehicle_id: Optional[UUID]
    vehicle_label: Optional[str]
    technician: Optional[str]
    assigned_at: Optional[datetime]
    installed_at: Optional[datetime]
    unassigned_at: Optional[datetime]
    installation_location: Optional[str]
    installation_latitude: Optional[float]
    installation_longitude: Optional[float]
    asset_label: Optional[str]
    asset_registration: Optional[str]
    notes: Optional[str]
    is_active: bool
    sim_id: Optional[int] = None
    sim_iccid: Optional[str] = None
    sim_msisdn: Optional[str] = None
    sim_carrier: Optional[str] = None
    sim_roaming_enabled: Optional[bool] = None


class SimAssignmentInfo(BaseModel):
    """Current SIM assignment details."""

    target: str
    hardware_id: Optional[int]
    hardware_imei: Optional[str]
    hub_id: Optional[UUID]
    hub_name: Optional[str]
    vehicle_id: Optional[UUID]
    vehicle_label: Optional[str]
    assigned_at: Optional[datetime]
    technician: Optional[str]
    notes: Optional[str]


class SimAssignmentHistoryItem(BaseModel):
    """Historical SIM assignment entry."""

    id: int
    target: str
    hardware_id: Optional[int]
    hardware_imei: Optional[str]
    hub_id: Optional[UUID]
    hub_name: Optional[str]
    vehicle_id: Optional[UUID]
    vehicle_label: Optional[str]
    technician: Optional[str]
    assigned_at: Optional[datetime]
    unassigned_at: Optional[datetime]
    notes: Optional[str]
    is_active: bool


class SimInventoryItem(BaseModel):
    """Flattened representation of a SIM inventory record."""

    id: int
    iccid: str
    msisdn: Optional[str]
    carrier: Optional[str]
    imsi: Optional[str]
    roaming_enabled: bool = False
    roaming_regions: Optional[str]
    status: SimStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    assignment: Optional[SimAssignmentInfo]
    assignment_history: list[SimAssignmentHistoryItem] = []

    model_config = ConfigDict(from_attributes=True)


class SimInventoryData(BaseModel):
    items: list[SimInventoryItem]


class SimInventorySummary(BaseModel):
    total: int
    visible: int
    updated_at: datetime
    status_counts: Dict[str, int]


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    page: int
    per_page: int
    total: int


class SimInventoryListResponse(BaseModel):
    data: SimInventoryData
    summary: SimInventorySummary
    meta: PaginationMeta


class SimInventoryDetailResponse(BaseModel):
    data: SimInventoryItem


class DevicePairingInfo(BaseModel):
    """Latest pairing workflow metadata."""

    status: Optional[str]
    requested_by: Optional[str]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    notes: Optional[str]


class DeviceInventoryItem(BaseModel):
    """Flattened representation of a hardware inventory record."""

    id: int
    imei: str
    serial_number: Optional[str]
    hardware_type: Optional[str]
    model: Optional[str]
    manufacturer: Optional[str]
    firmware_version: Optional[str]
    status: HardwareStatus
    notes: Optional[str]
    purchase_date: Optional[datetime]
    purchase_cost: Optional[float]
    created_at: datetime
    updated_at: datetime
    last_seen_at: Optional[datetime]
    assignment: Optional[DeviceAssignment]
    assignment_history: list[DeviceAssignmentHistoryItem] = []
    sim: Optional[SimInventoryItem] = None
    pairing: Optional[DevicePairingInfo]

    model_config = ConfigDict(from_attributes=True)


class DeviceInventoryData(BaseModel):
    """Container for list responses."""

    items: list[DeviceInventoryItem]


class DeviceInventorySummary(BaseModel):
    """Counts used for UI distribution widgets."""

    total: int
    visible: int
    updated_at: datetime
    status_counts: Dict[str, int]


class DeviceInventoryListResponse(BaseModel):
    """List payload consumed by the admin UI."""

    data: DeviceInventoryData
    summary: DeviceInventorySummary
    meta: PaginationMeta


class DeviceInventoryDetailResponse(BaseModel):
    """Detail payload for a single device."""

    data: DeviceInventoryItem


class DeviceInventoryUpdateRequest(BaseModel):
    """Partial update payload for inventory records."""

    status: Optional[HardwareStatus] = None
    firmware_version: Optional[str] = None
    hardware_type: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[datetime] = None
    notes: Optional[str] = None


class DeviceStatusUpdateRequest(BaseModel):
    """Request body for lifecycle updates."""

    status: HardwareStatus
    notes: Optional[str] = None


class DeviceAssignmentRequest(BaseModel):
    """Request body for assignment actions."""

    hub_id: Optional[UUID] = None
    vehicle_id: Optional[UUID] = None
    source_job_id: Optional[str] = None
    asset_type: Optional[str] = None
    asset_name: Optional[str] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_year: Optional[str] = None
    engine_capacity: Optional[str] = None
    vin: Optional[str] = None
    technician: Optional[str] = None
    installed_at: Optional[datetime] = None
    installation_location: Optional[str] = None
    installation_latitude: Optional[float] = None
    installation_longitude: Optional[float] = None
    asset_label: Optional[str] = None
    asset_registration: Optional[str] = None
    sim_id: Optional[int] = None
    reassignment_reason: Optional[str] = None
    notes: Optional[str] = None


class DeviceReassignmentRequest(BaseModel):
    """Request body for recall/replacement workflow."""

    replacement_hardware_id: int
    asset_type: Optional[str] = None
    asset_name: Optional[str] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_year: Optional[str] = None
    engine_capacity: Optional[str] = None
    vin: Optional[str] = None
    technician: Optional[str] = None
    installed_at: Optional[datetime] = None
    installation_location: Optional[str] = None
    installation_latitude: Optional[float] = None
    installation_longitude: Optional[float] = None
    asset_label: Optional[str] = None
    asset_registration: Optional[str] = None
    faulty_reason: Optional[str] = None
    notes: Optional[str] = None


class DeviceRecallRequest(BaseModel):
    """Request body for recalling installed hardware back into inventory."""

    status: HardwareStatus = HardwareStatus.IN_STOCK
    reason: str
    source_job_id: Optional[str] = None
    notes: Optional[str] = None


class SimInventoryCreateRequest(BaseModel):
    """Request body for new SIM intake."""

    iccid: str
    msisdn: Optional[str] = None
    carrier: Optional[str] = "Econet"
    imsi: Optional[str] = None
    roaming_enabled: bool = False
    roaming_regions: Optional[str] = None
    notes: Optional[str] = None


class SimInventoryUpdateRequest(BaseModel):
    """Partial update payload for SIM inventory records."""

    msisdn: Optional[str] = None
    carrier: Optional[str] = None
    imsi: Optional[str] = None
    roaming_enabled: Optional[bool] = None
    roaming_regions: Optional[str] = None
    status: Optional[SimStatus] = None
    notes: Optional[str] = None


class SimAssignmentRequest(BaseModel):
    """Assign a SIM to a hardware tracker."""

    hardware_id: int
    hub_id: Optional[UUID] = None
    vehicle_id: Optional[UUID] = None
    source_job_id: Optional[str] = None
    notes: Optional[str] = None


class SimRecallRequest(BaseModel):
    """Recall a SIM back into inventory or suspend it."""

    status: SimStatus = SimStatus.IN_STOCK
    reason: str
    source_job_id: Optional[str] = None
    notes: Optional[str] = None


class DeviceIntakeRequest(BaseModel):
    """Request body for new hardware intake."""

    imei: str
    hardware_type: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    firmware_version: Optional[str] = None
    serial_number: Optional[str] = None
    notes: Optional[str] = None
    purchase_date: Optional[datetime] = None
