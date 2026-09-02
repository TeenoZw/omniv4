"""Schemas for technician workflow board APIs."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.technician_job import TechnicianJobPriority, TechnicianJobStatus


class TechnicianJobItem(BaseModel):
    """Serialized technician job card."""

    id: UUID
    hub_id: UUID
    hub_code: Optional[str] = None
    hub_name: Optional[str] = None
    hardware_id: Optional[int] = None
    hardware_imei: Optional[str] = None
    hardware_model: Optional[str] = None
    vehicle_id: Optional[UUID] = None
    assigned_technician_id: Optional[UUID] = None
    assigned_technician_name: Optional[str] = None
    assigned_technician_email: Optional[str] = None
    requested_by_id: Optional[UUID] = None
    requested_by_name: Optional[str] = None
    status: TechnicianJobStatus
    priority: TechnicianJobPriority
    scheduled_for: Optional[datetime] = None
    started_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    declined_at: Optional[datetime] = None
    installed_at: Optional[datetime] = None
    installation_location: Optional[str] = None
    installation_latitude: Optional[float] = None
    installation_longitude: Optional[float] = None
    asset_label: Optional[str] = None
    asset_registration: Optional[str] = None
    notes: Optional[str] = None
    completion_notes: Optional[str] = None
    decline_reason: Optional[str] = None
    assignment_reference: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TechnicianJobsListResponse(BaseModel):
    """Paginated list response."""

    items: list[TechnicianJobItem]
    meta: dict


class TechnicianJobCreateRequest(BaseModel):
    """Admin payload for creating a job card."""

    hub_id: UUID
    hardware_id: Optional[int] = None
    vehicle_id: Optional[UUID] = None
    assigned_technician_id: Optional[UUID] = None
    priority: TechnicianJobPriority = TechnicianJobPriority.normal
    scheduled_for: Optional[datetime] = None
    installed_at: Optional[datetime] = None
    installation_location: Optional[str] = Field(default=None, max_length=255)
    installation_latitude: Optional[float] = None
    installation_longitude: Optional[float] = None
    asset_label: Optional[str] = Field(default=None, max_length=255)
    asset_registration: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = None


class TechnicianJobUpdateRequest(BaseModel):
    """Patch payload for admin/technician actions."""

    status: Optional[TechnicianJobStatus] = None
    assigned_technician_id: Optional[UUID] = None
    priority: Optional[TechnicianJobPriority] = None
    scheduled_for: Optional[datetime] = None
    installed_at: Optional[datetime] = None
    installation_location: Optional[str] = Field(default=None, max_length=255)
    installation_latitude: Optional[float] = None
    installation_longitude: Optional[float] = None
    asset_label: Optional[str] = Field(default=None, max_length=255)
    asset_registration: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = None
    completion_notes: Optional[str] = None
    decline_reason: Optional[str] = None
