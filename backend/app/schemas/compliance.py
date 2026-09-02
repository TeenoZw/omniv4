"""Schemas for operational compliance registers."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class PaginationMeta(BaseModel):
    page: int
    per_page: int
    total: int


class ComplianceAttachmentItem(BaseModel):
    id: int
    title: Optional[str] = None
    description: Optional[str] = None
    original_filename: str
    mime_type: Optional[str] = None
    size_bytes: int
    uploaded_by: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComplianceAttachmentUploadResponse(BaseModel):
    data: ComplianceAttachmentItem


class ComplianceOverviewCard(BaseModel):
    total: int = 0
    open: int = 0
    overdue: int = 0
    recent_updates: int = 0
    attachments: int = 0


class ComplianceOverviewIncidentCard(BaseModel):
    total: int = 0
    open: int = 0
    critical_open: int = 0
    notification_required: int = 0
    attachments: int = 0


class ComplianceOverviewRecentItem(BaseModel):
    id: int
    reference_no: str
    title: str
    status: str
    updated_at: datetime


class ComplianceOverviewResponse(BaseModel):
    generated_at: datetime
    requests: ComplianceOverviewCard
    incidents: ComplianceOverviewIncidentCard
    recent_requests: list[ComplianceOverviewRecentItem]
    recent_incidents: list[ComplianceOverviewRecentItem]


class DataSubjectRequestBase(BaseModel):
    request_type: str = Field(
        ...,
        pattern=r"^(access|correction|deletion|objection|portability|complaint|marketing_objection|other)$",
    )
    requester_name: str
    data_subject_name: Optional[str] = None
    requester_email: Optional[str] = None
    requester_phone: Optional[str] = None
    channel: Optional[str] = None
    identity_verified: bool = False
    summary: str
    assigned_owner: Optional[str] = None
    due_date: Optional[datetime] = None
    decision: Optional[str] = None
    responded_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    legal_basis: Optional[str] = None
    notes: Optional[str] = None


class DataSubjectRequestCreate(DataSubjectRequestBase):
    status: str = Field(
        default="new",
        pattern=r"^(new|in_review|awaiting_identity|approved|rejected|fulfilled|closed)$",
    )


class DataSubjectRequestUpdate(BaseModel):
    request_type: Optional[str] = Field(
        default=None,
        pattern=r"^(access|correction|deletion|objection|portability|complaint|marketing_objection|other)$",
    )
    status: Optional[str] = Field(
        default=None,
        pattern=r"^(new|in_review|awaiting_identity|approved|rejected|fulfilled|closed)$",
    )
    requester_name: Optional[str] = None
    data_subject_name: Optional[str] = None
    requester_email: Optional[str] = None
    requester_phone: Optional[str] = None
    channel: Optional[str] = None
    identity_verified: Optional[bool] = None
    summary: Optional[str] = None
    assigned_owner: Optional[str] = None
    due_date: Optional[datetime] = None
    decision: Optional[str] = None
    responded_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    legal_basis: Optional[str] = None
    notes: Optional[str] = None


class DataSubjectRequestItem(DataSubjectRequestBase):
    id: int
    reference_no: str
    status: str
    attachment_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DataSubjectRequestDetailItem(DataSubjectRequestItem):
    attachments: list[ComplianceAttachmentItem] = []


class DataSubjectRequestData(BaseModel):
    items: list[DataSubjectRequestItem]


class DataSubjectRequestSummary(BaseModel):
    total: int
    visible: int
    updated_at: datetime
    status_counts: Dict[str, int]


class DataSubjectRequestListResponse(BaseModel):
    data: DataSubjectRequestData
    summary: DataSubjectRequestSummary
    meta: PaginationMeta


class DataSubjectRequestDetailResponse(BaseModel):
    data: DataSubjectRequestDetailItem


class SecurityIncidentBase(BaseModel):
    incident_type: str = Field(
        ...,
        pattern=r"^(unauthorised_access|data_breach|device_loss|credential_compromise|service_outage|operator_issue|other)$",
    )
    status: str = Field(default="open", pattern=r"^(open|contained|investigating|notified|closed)$")
    severity: str = Field(default="medium", pattern=r"^(low|medium|high|critical)$")
    reported_by: Optional[str] = None
    systems_affected: Optional[str] = None
    information_affected: Optional[str] = None
    summary: str
    containment_action: Optional[str] = None
    impact_assessment: Optional[str] = None
    owner: Optional[str] = None
    information_officer_notified: bool = False
    regulator_notification_required: bool = False
    data_subject_notification_required: bool = False
    regulator_notified_at: Optional[datetime] = None
    data_subjects_notified_at: Optional[datetime] = None
    detected_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    lessons_learned: Optional[str] = None
    notes: Optional[str] = None


class SecurityIncidentCreate(SecurityIncidentBase):
    pass


class SecurityIncidentUpdate(BaseModel):
    incident_type: Optional[str] = Field(
        default=None,
        pattern=r"^(unauthorised_access|data_breach|device_loss|credential_compromise|service_outage|operator_issue|other)$",
    )
    status: Optional[str] = Field(default=None, pattern=r"^(open|contained|investigating|notified|closed)$")
    severity: Optional[str] = Field(default=None, pattern=r"^(low|medium|high|critical)$")
    reported_by: Optional[str] = None
    systems_affected: Optional[str] = None
    information_affected: Optional[str] = None
    summary: Optional[str] = None
    containment_action: Optional[str] = None
    impact_assessment: Optional[str] = None
    owner: Optional[str] = None
    information_officer_notified: Optional[bool] = None
    regulator_notification_required: Optional[bool] = None
    data_subject_notification_required: Optional[bool] = None
    regulator_notified_at: Optional[datetime] = None
    data_subjects_notified_at: Optional[datetime] = None
    detected_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    lessons_learned: Optional[str] = None
    notes: Optional[str] = None


class SecurityIncidentItem(SecurityIncidentBase):
    id: int
    reference_no: str
    attachment_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SecurityIncidentDetailItem(SecurityIncidentItem):
    attachments: list[ComplianceAttachmentItem] = []


class SecurityIncidentData(BaseModel):
    items: list[SecurityIncidentItem]


class SecurityIncidentSummary(BaseModel):
    total: int
    visible: int
    updated_at: datetime
    status_counts: Dict[str, int]


class SecurityIncidentListResponse(BaseModel):
    data: SecurityIncidentData
    summary: SecurityIncidentSummary
    meta: PaginationMeta


class SecurityIncidentDetailResponse(BaseModel):
    data: SecurityIncidentDetailItem
