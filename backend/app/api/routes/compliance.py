"""Operational compliance register routes."""
from __future__ import annotations

from collections import Counter
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, Response
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.auth import require_role
from app.core.database import get_db
from app.models.compliance import ComplianceAttachment, DataSubjectRequest, SecurityIncident
from app.models.user import User, UserRole
from app.schemas.compliance import (
    ComplianceAttachmentItem,
    ComplianceAttachmentUploadResponse,
    ComplianceOverviewCard,
    ComplianceOverviewIncidentCard,
    ComplianceOverviewRecentItem,
    ComplianceOverviewResponse,
    DataSubjectRequestCreate,
    DataSubjectRequestData,
    DataSubjectRequestDetailItem,
    DataSubjectRequestDetailResponse,
    DataSubjectRequestItem,
    DataSubjectRequestListResponse,
    DataSubjectRequestSummary,
    DataSubjectRequestUpdate,
    PaginationMeta,
    SecurityIncidentCreate,
    SecurityIncidentData,
    SecurityIncidentDetailItem,
    SecurityIncidentDetailResponse,
    SecurityIncidentItem,
    SecurityIncidentListResponse,
    SecurityIncidentSummary,
    SecurityIncidentUpdate,
)
from app.services.admin_activity import append_admin_activity
from app.services.compliance_exports import (
    attachment_disk_path,
    compliance_storage_root,
    incident_export_pack,
    incident_pdf_bytes,
    record_csv_bytes,
    request_export_pack,
    request_pdf_bytes,
)

router = APIRouter(prefix="/compliance", tags=["compliance"])
MAX_ATTACHMENT_BYTES = 15 * 1024 * 1024


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _ref(prefix: str) -> str:
    stamp = _utcnow().strftime("%Y%m%d")
    return f"{prefix}-{stamp}-{uuid4().hex[:6].upper()}"


def _iso(value: datetime | None) -> str:
    return value.isoformat() if value else ""


def _audit_payload(message: str, **metadata: object) -> str:
    payload = {"message": message}
    payload.update({key: value for key, value in metadata.items() if value not in (None, "", [], {})})
    return json.dumps(payload, separators=(",", ":"), default=str)


def _serialize_attachment(item: ComplianceAttachment) -> ComplianceAttachmentItem:
    return ComplianceAttachmentItem.model_validate(item)


def _request_attachment_counts(db: Session, ids: list[int]) -> dict[int, int]:
    if not ids:
        return {}
    rows = (
        db.query(ComplianceAttachment.data_subject_request_id, func.count(ComplianceAttachment.id))
        .filter(ComplianceAttachment.data_subject_request_id.in_(ids))
        .group_by(ComplianceAttachment.data_subject_request_id)
        .all()
    )
    return {request_id: int(count) for request_id, count in rows if request_id is not None}


def _incident_attachment_counts(db: Session, ids: list[int]) -> dict[int, int]:
    if not ids:
        return {}
    rows = (
        db.query(ComplianceAttachment.security_incident_id, func.count(ComplianceAttachment.id))
        .filter(ComplianceAttachment.security_incident_id.in_(ids))
        .group_by(ComplianceAttachment.security_incident_id)
        .all()
    )
    return {incident_id: int(count) for incident_id, count in rows if incident_id is not None}


def _serialize_request(item: DataSubjectRequest, attachment_count: int = 0) -> DataSubjectRequestItem:
    data = DataSubjectRequestItem.model_validate(item).model_dump()
    data["attachment_count"] = attachment_count
    return DataSubjectRequestItem.model_validate(data)


def _serialize_incident(item: SecurityIncident, attachment_count: int = 0) -> SecurityIncidentItem:
    data = SecurityIncidentItem.model_validate(item).model_dump()
    data["attachment_count"] = attachment_count
    return SecurityIncidentItem.model_validate(data)


def _request_detail(item: DataSubjectRequest, db: Session) -> DataSubjectRequestDetailItem:
    attachments = (
        db.query(ComplianceAttachment)
        .filter(ComplianceAttachment.data_subject_request_id == item.id)
        .order_by(ComplianceAttachment.created_at.desc())
        .all()
    )
    data = DataSubjectRequestDetailItem.model_validate(item).model_dump()
    data["attachment_count"] = len(attachments)
    data["attachments"] = [_serialize_attachment(attachment) for attachment in attachments]
    return DataSubjectRequestDetailItem.model_validate(data)


def _incident_detail(item: SecurityIncident, db: Session) -> SecurityIncidentDetailItem:
    attachments = (
        db.query(ComplianceAttachment)
        .filter(ComplianceAttachment.security_incident_id == item.id)
        .order_by(ComplianceAttachment.created_at.desc())
        .all()
    )
    data = SecurityIncidentDetailItem.model_validate(item).model_dump()
    data["attachment_count"] = len(attachments)
    data["attachments"] = [_serialize_attachment(attachment) for attachment in attachments]
    return SecurityIncidentDetailItem.model_validate(data)


def _request_summary(items: list[DataSubjectRequest], visible: int) -> DataSubjectRequestSummary:
    counts = Counter(item.status for item in items if item.status)
    updated_at = max((item.updated_at for item in items if item.updated_at), default=_utcnow())
    return DataSubjectRequestSummary(
        total=len(items),
        visible=visible,
        updated_at=updated_at,
        status_counts=dict(sorted(counts.items())),
    )


def _incident_summary(items: list[SecurityIncident], visible: int) -> SecurityIncidentSummary:
    counts = Counter(item.status for item in items if item.status)
    updated_at = max((item.updated_at for item in items if item.updated_at), default=_utcnow())
    return SecurityIncidentSummary(
        total=len(items),
        visible=visible,
        updated_at=updated_at,
        status_counts=dict(sorted(counts.items())),
    )


def _sanitize_filename(filename: str) -> str:
    safe = Path(filename or "evidence").name
    return safe.replace("\x00", "").strip() or "evidence"


def _store_attachment(upload: UploadFile, file_bytes: bytes) -> tuple[str, Path]:
    filename = _sanitize_filename(upload.filename or "evidence")
    suffix = Path(filename).suffix[:16]
    stored = f"{uuid4().hex}{suffix}"
    path = compliance_storage_root() / stored
    path.write_bytes(file_bytes)
    return stored, path


async def _create_attachment(
    *,
    upload: UploadFile,
    actor: User,
    db: Session,
    request: DataSubjectRequest | None = None,
    incident: SecurityIncident | None = None,
    title: str | None = None,
    description: str | None = None,
) -> ComplianceAttachment:
    file_bytes = await upload.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attachment file is empty")
    if len(file_bytes) > MAX_ATTACHMENT_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Attachment exceeds 15 MB")

    stored_filename, path = _store_attachment(upload, file_bytes)
    try:
        attachment = ComplianceAttachment(
            data_subject_request_id=request.id if request else None,
            security_incident_id=incident.id if incident else None,
            title=(title or "").strip() or None,
            description=(description or "").strip() or None,
            original_filename=_sanitize_filename(upload.filename or "evidence"),
            stored_filename=stored_filename,
            mime_type=(upload.content_type or "application/octet-stream").strip() or "application/octet-stream",
            size_bytes=len(file_bytes),
            uploaded_by=actor.email,
        )
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        return attachment
    except Exception:
        path.unlink(missing_ok=True)
        db.rollback()
        raise


@router.get("/overview", response_model=ComplianceOverviewResponse)
def get_compliance_overview(
    _: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    now = _utcnow()
    recent_cutoff = now - timedelta(days=7)

    requests_total = db.query(func.count(DataSubjectRequest.id)).scalar() or 0
    requests_open = (
        db.query(func.count(DataSubjectRequest.id))
        .filter(DataSubjectRequest.status.in_(["new", "in_review", "awaiting_identity", "approved"]))
        .scalar()
        or 0
    )
    requests_overdue = (
        db.query(func.count(DataSubjectRequest.id))
        .filter(
            DataSubjectRequest.status.in_(["new", "in_review", "awaiting_identity", "approved"]),
            DataSubjectRequest.due_date.isnot(None),
            DataSubjectRequest.due_date < now,
        )
        .scalar()
        or 0
    )
    requests_recent = (
        db.query(func.count(DataSubjectRequest.id)).filter(DataSubjectRequest.updated_at >= recent_cutoff).scalar() or 0
    )
    request_attachments = (
        db.query(func.count(ComplianceAttachment.id))
        .filter(ComplianceAttachment.data_subject_request_id.isnot(None))
        .scalar()
        or 0
    )

    incidents_total = db.query(func.count(SecurityIncident.id)).scalar() or 0
    incidents_open = (
        db.query(func.count(SecurityIncident.id))
        .filter(SecurityIncident.status.in_(["open", "contained", "investigating", "notified"]))
        .scalar()
        or 0
    )
    incidents_critical = (
        db.query(func.count(SecurityIncident.id))
        .filter(SecurityIncident.status != "closed", SecurityIncident.severity == "critical")
        .scalar()
        or 0
    )
    incidents_notification = (
        db.query(func.count(SecurityIncident.id))
        .filter(
            SecurityIncident.status != "closed",
            or_(
                SecurityIncident.regulator_notification_required.is_(True),
                SecurityIncident.data_subject_notification_required.is_(True),
            ),
        )
        .scalar()
        or 0
    )
    incident_attachments = (
        db.query(func.count(ComplianceAttachment.id))
        .filter(ComplianceAttachment.security_incident_id.isnot(None))
        .scalar()
        or 0
    )

    recent_requests = (
        db.query(DataSubjectRequest)
        .order_by(DataSubjectRequest.updated_at.desc(), DataSubjectRequest.created_at.desc())
        .limit(5)
        .all()
    )
    recent_incidents = (
        db.query(SecurityIncident)
        .order_by(SecurityIncident.updated_at.desc(), SecurityIncident.created_at.desc())
        .limit(5)
        .all()
    )

    return ComplianceOverviewResponse(
        generated_at=now,
        requests=ComplianceOverviewCard(
            total=int(requests_total),
            open=int(requests_open),
            overdue=int(requests_overdue),
            recent_updates=int(requests_recent),
            attachments=int(request_attachments),
        ),
        incidents=ComplianceOverviewIncidentCard(
            total=int(incidents_total),
            open=int(incidents_open),
            critical_open=int(incidents_critical),
            notification_required=int(incidents_notification),
            attachments=int(incident_attachments),
        ),
        recent_requests=[
            ComplianceOverviewRecentItem(
                id=item.id,
                reference_no=item.reference_no,
                title=item.requester_name,
                status=item.status,
                updated_at=item.updated_at,
            )
            for item in recent_requests
        ],
        recent_incidents=[
            ComplianceOverviewRecentItem(
                id=item.id,
                reference_no=item.reference_no,
                title=item.summary[:80] if item.summary else item.incident_type,
                status=item.status,
                updated_at=item.updated_at,
            )
            for item in recent_incidents
        ],
    )


@router.get("/requests", response_model=DataSubjectRequestListResponse)
def list_data_subject_requests(
    search: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    request_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=200),
    _: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    query = db.query(DataSubjectRequest)
    if status_filter and status_filter != "all":
        query = query.filter(DataSubjectRequest.status == status_filter)
    if request_type and request_type != "all":
        query = query.filter(DataSubjectRequest.request_type == request_type)
    if search and search.strip():
        needle = f"%{search.strip()}%"
        query = query.filter(
            or_(
                DataSubjectRequest.reference_no.ilike(needle),
                DataSubjectRequest.requester_name.ilike(needle),
                DataSubjectRequest.data_subject_name.ilike(needle),
                DataSubjectRequest.requester_email.ilike(needle),
                DataSubjectRequest.summary.ilike(needle),
                DataSubjectRequest.assigned_owner.ilike(needle),
            )
        )

    summary_items = query.order_by(None).all()
    total = len(summary_items)
    items = (
        query.order_by(DataSubjectRequest.updated_at.desc(), DataSubjectRequest.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    counts = _request_attachment_counts(db, [item.id for item in items])
    summary = _request_summary(summary_items, len(items))
    return DataSubjectRequestListResponse(
        data=DataSubjectRequestData(items=[_serialize_request(item, counts.get(item.id, 0)) for item in items]),
        summary=summary,
        meta=PaginationMeta(page=page, per_page=limit, total=total),
    )


@router.get("/requests/export.csv")
def export_data_subject_requests_csv(
    search: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    request_type: str | None = Query(default=None),
    _: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    query = db.query(DataSubjectRequest)
    if status_filter and status_filter != "all":
        query = query.filter(DataSubjectRequest.status == status_filter)
    if request_type and request_type != "all":
        query = query.filter(DataSubjectRequest.request_type == request_type)
    if search and search.strip():
        needle = f"%{search.strip()}%"
        query = query.filter(
            or_(
                DataSubjectRequest.reference_no.ilike(needle),
                DataSubjectRequest.requester_name.ilike(needle),
                DataSubjectRequest.data_subject_name.ilike(needle),
                DataSubjectRequest.requester_email.ilike(needle),
                DataSubjectRequest.summary.ilike(needle),
                DataSubjectRequest.assigned_owner.ilike(needle),
            )
        )
    items = query.order_by(DataSubjectRequest.updated_at.desc(), DataSubjectRequest.created_at.desc()).all()
    csv_bytes = record_csv_bytes(
        [
            "reference_no",
            "request_type",
            "status",
            "requester_name",
            "data_subject_name",
            "requester_email",
            "assigned_owner",
            "due_date",
            "updated_at",
        ],
        [
            [
                item.reference_no,
                item.request_type,
                item.status,
                item.requester_name,
                item.data_subject_name or "",
                item.requester_email or "",
                item.assigned_owner or "",
                _iso(item.due_date),
                _iso(item.updated_at),
            ]
            for item in items
        ],
    )
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="omni-data-subject-requests.csv"'},
    )


@router.post("/requests", response_model=DataSubjectRequestDetailResponse, status_code=status.HTTP_201_CREATED)
def create_data_subject_request(
    payload: DataSubjectRequestCreate,
    actor: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    item = DataSubjectRequest(reference_no=_ref("DSR"), **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    append_admin_activity(
        db,
        module="compliance",
        change="Data subject request created",
        details=_audit_payload(
            f"{item.reference_no} opened as {item.request_type}",
            reference_no=item.reference_no,
            record_type="data_subject_request",
            record_id=item.id,
            request_type=item.request_type,
            status=item.status,
        ),
        actor=actor,
        target_type="data_subject_request",
        target_id=str(item.id),
    )
    return DataSubjectRequestDetailResponse(data=_request_detail(item, db))


@router.get("/requests/{request_id}", response_model=DataSubjectRequestDetailResponse)
def get_data_subject_request(
    request_id: int,
    _: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    item = db.query(DataSubjectRequest).filter(DataSubjectRequest.id == request_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data subject request not found")
    return DataSubjectRequestDetailResponse(data=_request_detail(item, db))


@router.patch("/requests/{request_id}", response_model=DataSubjectRequestDetailResponse)
def update_data_subject_request(
    request_id: int,
    payload: DataSubjectRequestUpdate,
    actor: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    item = db.query(DataSubjectRequest).filter(DataSubjectRequest.id == request_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data subject request not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    append_admin_activity(
        db,
        module="compliance",
        change="Data subject request updated",
        details=_audit_payload(
            f"{item.reference_no} moved to {item.status}",
            reference_no=item.reference_no,
            record_type="data_subject_request",
            record_id=item.id,
            request_type=item.request_type,
            status=item.status,
        ),
        actor=actor,
        target_type="data_subject_request",
        target_id=str(item.id),
    )
    return DataSubjectRequestDetailResponse(data=_request_detail(item, db))


@router.post("/requests/{request_id}/attachments", response_model=ComplianceAttachmentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_data_subject_request_attachment(
    request_id: int,
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    description: str | None = Form(default=None),
    actor: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    item = db.query(DataSubjectRequest).filter(DataSubjectRequest.id == request_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data subject request not found")
    attachment = await _create_attachment(
        upload=file,
        actor=actor,
        db=db,
        request=item,
        title=title,
        description=description,
    )
    append_admin_activity(
        db,
        module="compliance",
        change="Request evidence attached",
        details=_audit_payload(
            f"{attachment.original_filename} added to {item.reference_no}",
            reference_no=item.reference_no,
            record_type="data_subject_request",
            record_id=item.id,
            attachment_id=attachment.id,
            attachment_name=attachment.original_filename,
            attachment_title=attachment.title,
            attachment_mime=attachment.mime_type,
            attachment_description=attachment.description,
        ),
        actor=actor,
        target_type="data_subject_request",
        target_id=str(item.id),
    )
    return ComplianceAttachmentUploadResponse(data=_serialize_attachment(attachment))


@router.get("/requests/{request_id}/export.pdf")
def export_data_subject_request_pdf(
    request_id: int,
    _: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    item = db.query(DataSubjectRequest).filter(DataSubjectRequest.id == request_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data subject request not found")
    attachments = (
        db.query(ComplianceAttachment)
        .filter(ComplianceAttachment.data_subject_request_id == item.id)
        .order_by(ComplianceAttachment.created_at.desc())
        .all()
    )
    pdf_bytes = request_pdf_bytes(item, attachments)
    filename = f"{item.reference_no.lower()}-summary.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/requests/{request_id}/export-pack")
def export_data_subject_request_pack(
    request_id: int,
    _: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    item = db.query(DataSubjectRequest).filter(DataSubjectRequest.id == request_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data subject request not found")
    attachments = (
        db.query(ComplianceAttachment)
        .filter(ComplianceAttachment.data_subject_request_id == item.id)
        .order_by(ComplianceAttachment.created_at.desc())
        .all()
    )
    pack = request_export_pack(item, attachments)
    filename = f"{item.reference_no.lower()}-evidence-pack.zip"
    return Response(
        content=pack,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/incidents", response_model=SecurityIncidentListResponse)
def list_security_incidents(
    search: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    severity: str | None = Query(default=None),
    incident_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=200),
    _: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    query = db.query(SecurityIncident)
    if status_filter and status_filter != "all":
        query = query.filter(SecurityIncident.status == status_filter)
    if severity and severity != "all":
        query = query.filter(SecurityIncident.severity == severity)
    if incident_type and incident_type != "all":
        query = query.filter(SecurityIncident.incident_type == incident_type)
    if search and search.strip():
        needle = f"%{search.strip()}%"
        query = query.filter(
            or_(
                SecurityIncident.reference_no.ilike(needle),
                SecurityIncident.reported_by.ilike(needle),
                SecurityIncident.summary.ilike(needle),
                SecurityIncident.owner.ilike(needle),
                SecurityIncident.systems_affected.ilike(needle),
                SecurityIncident.information_affected.ilike(needle),
            )
        )

    summary_items = query.order_by(None).all()
    total = len(summary_items)
    items = (
        query.order_by(SecurityIncident.updated_at.desc(), SecurityIncident.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    counts = _incident_attachment_counts(db, [item.id for item in items])
    summary = _incident_summary(summary_items, len(items))
    return SecurityIncidentListResponse(
        data=SecurityIncidentData(items=[_serialize_incident(item, counts.get(item.id, 0)) for item in items]),
        summary=summary,
        meta=PaginationMeta(page=page, per_page=limit, total=total),
    )


@router.get("/incidents/export.csv")
def export_security_incidents_csv(
    search: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    severity: str | None = Query(default=None),
    incident_type: str | None = Query(default=None),
    _: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    query = db.query(SecurityIncident)
    if status_filter and status_filter != "all":
        query = query.filter(SecurityIncident.status == status_filter)
    if severity and severity != "all":
        query = query.filter(SecurityIncident.severity == severity)
    if incident_type and incident_type != "all":
        query = query.filter(SecurityIncident.incident_type == incident_type)
    if search and search.strip():
        needle = f"%{search.strip()}%"
        query = query.filter(
            or_(
                SecurityIncident.reference_no.ilike(needle),
                SecurityIncident.reported_by.ilike(needle),
                SecurityIncident.summary.ilike(needle),
                SecurityIncident.owner.ilike(needle),
                SecurityIncident.systems_affected.ilike(needle),
                SecurityIncident.information_affected.ilike(needle),
            )
        )
    items = query.order_by(SecurityIncident.updated_at.desc(), SecurityIncident.created_at.desc()).all()
    csv_bytes = record_csv_bytes(
        ["reference_no", "incident_type", "severity", "status", "owner", "reported_by", "detected_at", "updated_at"],
        [
            [
                item.reference_no,
                item.incident_type,
                item.severity,
                item.status,
                item.owner or "",
                item.reported_by or "",
                _iso(item.detected_at),
                _iso(item.updated_at),
            ]
            for item in items
        ],
    )
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="omni-security-incidents.csv"'},
    )


@router.post("/incidents", response_model=SecurityIncidentDetailResponse, status_code=status.HTTP_201_CREATED)
def create_security_incident(
    payload: SecurityIncidentCreate,
    actor: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    item = SecurityIncident(reference_no=_ref("SEC"), **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    append_admin_activity(
        db,
        module="compliance",
        change="Security incident created",
        details=_audit_payload(
            f"{item.reference_no} opened as {item.severity} severity",
            reference_no=item.reference_no,
            record_type="security_incident",
            record_id=item.id,
            incident_type=item.incident_type,
            severity=item.severity,
            status=item.status,
        ),
        actor=actor,
        target_type="security_incident",
        target_id=str(item.id),
    )
    return SecurityIncidentDetailResponse(data=_incident_detail(item, db))


@router.get("/incidents/{incident_id}", response_model=SecurityIncidentDetailResponse)
def get_security_incident(
    incident_id: int,
    _: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    item = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Security incident not found")
    return SecurityIncidentDetailResponse(data=_incident_detail(item, db))


@router.patch("/incidents/{incident_id}", response_model=SecurityIncidentDetailResponse)
def update_security_incident(
    incident_id: int,
    payload: SecurityIncidentUpdate,
    actor: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    item = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Security incident not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    append_admin_activity(
        db,
        module="compliance",
        change="Security incident updated",
        details=_audit_payload(
            f"{item.reference_no} moved to {item.status}",
            reference_no=item.reference_no,
            record_type="security_incident",
            record_id=item.id,
            incident_type=item.incident_type,
            severity=item.severity,
            status=item.status,
            regulator_notification_required=item.regulator_notification_required,
            data_subject_notification_required=item.data_subject_notification_required,
        ),
        actor=actor,
        target_type="security_incident",
        target_id=str(item.id),
    )
    return SecurityIncidentDetailResponse(data=_incident_detail(item, db))


@router.post("/incidents/{incident_id}/attachments", response_model=ComplianceAttachmentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_security_incident_attachment(
    incident_id: int,
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    description: str | None = Form(default=None),
    actor: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    item = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Security incident not found")
    attachment = await _create_attachment(
        upload=file,
        actor=actor,
        db=db,
        incident=item,
        title=title,
        description=description,
    )
    append_admin_activity(
        db,
        module="compliance",
        change="Incident evidence attached",
        details=_audit_payload(
            f"{attachment.original_filename} added to {item.reference_no}",
            reference_no=item.reference_no,
            record_type="security_incident",
            record_id=item.id,
            attachment_id=attachment.id,
            attachment_name=attachment.original_filename,
            attachment_title=attachment.title,
            attachment_mime=attachment.mime_type,
            attachment_description=attachment.description,
        ),
        actor=actor,
        target_type="security_incident",
        target_id=str(item.id),
    )
    return ComplianceAttachmentUploadResponse(data=_serialize_attachment(attachment))


@router.get("/incidents/{incident_id}/export.pdf")
def export_security_incident_pdf(
    incident_id: int,
    _: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    item = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Security incident not found")
    attachments = (
        db.query(ComplianceAttachment)
        .filter(ComplianceAttachment.security_incident_id == item.id)
        .order_by(ComplianceAttachment.created_at.desc())
        .all()
    )
    pdf_bytes = incident_pdf_bytes(item, attachments)
    filename = f"{item.reference_no.lower()}-summary.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/incidents/{incident_id}/export-pack")
def export_security_incident_pack(
    incident_id: int,
    _: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    item = db.query(SecurityIncident).filter(SecurityIncident.id == incident_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Security incident not found")
    attachments = (
        db.query(ComplianceAttachment)
        .filter(ComplianceAttachment.security_incident_id == item.id)
        .order_by(ComplianceAttachment.created_at.desc())
        .all()
    )
    pack = incident_export_pack(item, attachments)
    filename = f"{item.reference_no.lower()}-evidence-pack.zip"
    return Response(
        content=pack,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/attachments/{attachment_id}/download")
def download_compliance_attachment(
    attachment_id: int,
    _: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    attachment = db.query(ComplianceAttachment).filter(ComplianceAttachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    file_path = attachment_disk_path(attachment)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment file is missing on disk")
    return FileResponse(path=file_path, media_type=attachment.mime_type or "application/octet-stream", filename=attachment.original_filename)


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_compliance_attachment(
    attachment_id: int,
    actor: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    attachment = db.query(ComplianceAttachment).filter(ComplianceAttachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    parent_reference = attachment.request.reference_no if attachment.request else attachment.incident.reference_no if attachment.incident else str(attachment_id)
    target_type = "data_subject_request" if attachment.request else "security_incident"
    target_id = str(attachment.request.id if attachment.request else attachment.incident.id if attachment.incident else attachment_id)
    file_path = attachment_disk_path(attachment)
    db.delete(attachment)
    db.commit()
    file_path.unlink(missing_ok=True)
    append_admin_activity(
        db,
        module="compliance",
        change="Evidence attachment removed",
        details=_audit_payload(
            f"{attachment.original_filename} removed from {parent_reference}",
            reference_no=parent_reference,
            record_type=target_type,
            record_id=target_id,
            attachment_name=attachment.original_filename,
            attachment_mime=attachment.mime_type,
            attachment_description=attachment.description,
        ),
        actor=actor,
        target_type=target_type,
        target_id=target_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
