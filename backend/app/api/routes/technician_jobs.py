"""Technician workflow board routes."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.auth import require_role
from app.core.database import get_db
from app.models import Hub, User
from app.models.hardware import HardwareInventory, HardwareStatus
from app.models.technician_job import TechnicianJob, TechnicianJobPriority, TechnicianJobStatus
from app.models.user import UserRole
from app.schemas.technician_jobs import (
    TechnicianJobCreateRequest,
    TechnicianJobItem,
    TechnicianJobsListResponse,
    TechnicianJobUpdateRequest,
)
from app.services.admin_activity import append_admin_activity
from app.services.hardware import assign_hardware_to_vehicle

router = APIRouter(prefix="/technician-jobs", tags=["technician-jobs"])

READ_ROLES = (UserRole.admin, UserRole.technician)


def _is_admin(user: User) -> bool:
    return str(getattr(user.role, "value", user.role)).lower() == UserRole.admin.value


def _clean_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _to_float(value: Optional[Decimal | float]) -> Optional[float]:
    if value is None:
        return None
    return float(value)


def _serialize_job(job: TechnicianJob) -> TechnicianJobItem:
    return TechnicianJobItem(
        id=job.id,
        hub_id=job.hub_id,
        hub_code=job.hub.code if job.hub else None,
        hub_name=job.hub.name if job.hub else None,
        hardware_id=job.hardware_id,
        hardware_imei=job.hardware.imei if job.hardware else None,
        hardware_model=job.hardware.model if job.hardware else None,
        vehicle_id=job.vehicle_id,
        assigned_technician_id=job.assigned_technician_id,
        assigned_technician_name=job.assigned_technician.name if job.assigned_technician else None,
        assigned_technician_email=job.assigned_technician.email if job.assigned_technician else None,
        requested_by_id=job.requested_by,
        requested_by_name=job.requester.name if job.requester else None,
        status=job.status,
        priority=job.priority,
        scheduled_for=job.scheduled_for,
        started_at=job.started_at,
        accepted_at=job.accepted_at,
        completed_at=job.completed_at,
        cancelled_at=job.cancelled_at,
        declined_at=job.declined_at,
        installed_at=job.installed_at,
        installation_location=job.installation_location,
        installation_latitude=_to_float(job.installation_latitude),
        installation_longitude=_to_float(job.installation_longitude),
        asset_label=job.asset_label,
        asset_registration=job.asset_registration,
        notes=job.notes,
        completion_notes=job.completion_notes,
        decline_reason=job.decline_reason,
        assignment_reference=job.assignment_reference,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def _load_job_or_404(job_id: UUID, db: Session) -> TechnicianJob:
    job = (
        db.query(TechnicianJob)
        .options(
            joinedload(TechnicianJob.hub),
            joinedload(TechnicianJob.hardware),
            joinedload(TechnicianJob.requester),
            joinedload(TechnicianJob.assigned_technician),
        )
        .filter(TechnicianJob.id == job_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Technician job not found")
    return job


def _require_technician_user(db: Session, *, technician_id: UUID) -> User:
    technician_user = db.query(User).filter(User.id == technician_id).first()
    if not technician_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Technician user not found")
    user_role = str(getattr(technician_user.role, "value", technician_user.role)).lower()
    if user_role != UserRole.technician.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assigned user must be a technician")
    if not technician_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Technician account is inactive")
    return technician_user


@router.get("", response_model=TechnicianJobsListResponse)
async def list_technician_jobs(
    status_filter: Optional[TechnicianJobStatus] = Query(None, alias="status"),
    status_group: Optional[str] = Query(None, alias="status_group"),
    search: Optional[str] = Query(None, min_length=2),
    hub_id: Optional[UUID] = Query(None),
    technician_id: Optional[UUID] = Query(None),
    assigned_to_me: bool = Query(False),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=200),
    actor: User = Depends(require_role(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    """List technician workflow jobs with scoped access."""

    is_admin = _is_admin(actor)
    query = db.query(TechnicianJob).options(
        joinedload(TechnicianJob.hub),
        joinedload(TechnicianJob.hardware),
        joinedload(TechnicianJob.requester),
        joinedload(TechnicianJob.assigned_technician),
    )

    if is_admin:
        if hub_id:
            query = query.filter(TechnicianJob.hub_id == hub_id)
        if technician_id:
            query = query.filter(TechnicianJob.assigned_technician_id == technician_id)
        if assigned_to_me:
            query = query.filter(TechnicianJob.assigned_technician_id == actor.id)
    else:
        query = query.filter(
            TechnicianJob.assigned_technician_id == actor.id,
        )

    if status_filter is not None:
        query = query.filter(TechnicianJob.status == status_filter)
    elif status_group:
        normalized_group = status_group.strip().lower()
        if normalized_group == "open":
            query = query.filter(
                TechnicianJob.status.in_(
                    [
                        TechnicianJobStatus.pending,
                        TechnicianJobStatus.assigned,
                        TechnicianJobStatus.in_progress,
                    ]
                )
            )
        elif normalized_group == "assigned":
            query = query.filter(
                TechnicianJob.status == TechnicianJobStatus.assigned,
                TechnicianJob.accepted_at.is_(None),
                TechnicianJob.cancelled_at.is_(None),
            )
        elif normalized_group == "accepted":
            query = query.filter(
                TechnicianJob.status == TechnicianJobStatus.in_progress,
                TechnicianJob.accepted_at.is_not(None),
            )
        elif normalized_group == "closed":
            query = query.filter(TechnicianJob.status == TechnicianJobStatus.completed)
        elif normalized_group in {"cancelled", "declined"}:
            query = query.filter(TechnicianJob.status == TechnicianJobStatus.cancelled)
        elif normalized_group != "all":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported status_group. Use open, assigned, accepted, closed, declined, cancelled, or all.",
            )

    if search:
        pattern = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                func.lower(func.coalesce(TechnicianJob.asset_registration, "")).like(pattern),
                func.lower(func.coalesce(TechnicianJob.asset_label, "")).like(pattern),
                TechnicianJob.hub.has(func.lower(func.coalesce(Hub.name, "")).like(pattern)),
                TechnicianJob.hub.has(func.lower(func.coalesce(Hub.code, "")).like(pattern)),
                TechnicianJob.hardware.has(func.lower(func.coalesce(HardwareInventory.imei, "")).like(pattern)),
                TechnicianJob.hardware.has(func.lower(func.coalesce(HardwareInventory.model, "")).like(pattern)),
                TechnicianJob.assigned_technician.has(func.lower(func.coalesce(User.email, "")).like(pattern)),
                TechnicianJob.assigned_technician.has(func.lower(func.coalesce(User.name, "")).like(pattern)),
            )
        )

    total = query.count()
    jobs = (
        query.order_by(TechnicianJob.updated_at.desc(), TechnicianJob.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return TechnicianJobsListResponse(
        items=[_serialize_job(job) for job in jobs],
        meta={"page": page, "per_page": limit, "total": total},
    )


@router.post("", response_model=TechnicianJobItem, status_code=status.HTTP_201_CREATED)
async def create_technician_job(
    payload: TechnicianJobCreateRequest,
    actor: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    """Create a technician installation job card."""

    hub = db.query(Hub).filter(Hub.id == payload.hub_id, Hub.deleted_at.is_(None)).first()
    if not hub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hub not found")

    hardware = None
    if payload.hardware_id is not None:
        hardware = db.query(HardwareInventory).filter(HardwareInventory.id == payload.hardware_id).first()
        if not hardware:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hardware not found")

    assigned_technician = None
    next_status = TechnicianJobStatus.pending
    if payload.assigned_technician_id:
        assigned_technician = _require_technician_user(
            db,
            technician_id=payload.assigned_technician_id,
        )
        next_status = TechnicianJobStatus.assigned

    job = TechnicianJob(
        hub_id=payload.hub_id,
        hardware_id=payload.hardware_id,
        vehicle_id=payload.vehicle_id,
        requested_by=actor.id,
        assigned_technician_id=assigned_technician.id if assigned_technician else None,
        status=next_status,
        priority=payload.priority,
        scheduled_for=payload.scheduled_for,
        installed_at=payload.installed_at,
        installation_location=_clean_text(payload.installation_location),
        installation_latitude=payload.installation_latitude,
        installation_longitude=payload.installation_longitude,
        asset_label=_clean_text(payload.asset_label),
        asset_registration=_clean_text(payload.asset_registration),
        notes=_clean_text(payload.notes),
    )
    db.add(job)
    db.commit()
    job = _load_job_or_404(job.id, db)

    append_admin_activity(
        db,
        module="technician-workflow",
        change="Technician job created",
        details=(
            f"{hub.code} · "
            f"technician {assigned_technician.email if assigned_technician else 'unassigned'}"
            + (f" · hardware {hardware.imei}" if hardware else "")
        ),
        actor=actor,
        target_type="technician_job",
        target_id=str(job.id),
    )
    return _serialize_job(job)


@router.patch("/{job_id}", response_model=TechnicianJobItem)
async def update_technician_job(
    job_id: UUID,
    payload: TechnicianJobUpdateRequest,
    actor: User = Depends(require_role(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    """Update, start, complete, or reassign technician jobs."""

    job = _load_job_or_404(job_id, db)
    is_admin = _is_admin(actor)

    if not is_admin:
        if job.assigned_technician_id != actor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Job is not assigned to current technician")
        if job.status == TechnicianJobStatus.completed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Completed jobs are locked for technicians. Request an admin override.",
            )

    changed_fields: list[str] = []
    payload_fields = set(payload.model_fields_set)

    def apply_text(field_name: str, value: Optional[str]) -> None:
        if field_name not in payload_fields:
            return
        normalized = _clean_text(value)
        if getattr(job, field_name) != normalized:
            setattr(job, field_name, normalized)
            changed_fields.append(field_name)

    if "assigned_technician_id" in payload_fields:
        if not is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can reassign technicians")
        if payload.assigned_technician_id is None:
            if job.assigned_technician_id is not None:
                job.assigned_technician_id = None
                if job.status == TechnicianJobStatus.assigned:
                    job.status = TechnicianJobStatus.pending
                changed_fields.append("assigned_technician_id")
        else:
            technician = _require_technician_user(
                db,
                technician_id=payload.assigned_technician_id,
            )
            if job.assigned_technician_id != technician.id:
                job.assigned_technician_id = technician.id
                if job.status == TechnicianJobStatus.pending:
                    job.status = TechnicianJobStatus.assigned
                changed_fields.append("assigned_technician_id")

    if "priority" in payload_fields:
        if not is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can change priority")
        if payload.priority and job.priority != payload.priority:
            job.priority = payload.priority
            changed_fields.append("priority")

    if "scheduled_for" in payload_fields:
        if not is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can change schedule")
        if job.scheduled_for != payload.scheduled_for:
            job.scheduled_for = payload.scheduled_for
            changed_fields.append("scheduled_for")

    if "installed_at" in payload_fields and payload.installed_at != job.installed_at:
        job.installed_at = payload.installed_at
        changed_fields.append("installed_at")

    if "installation_latitude" in payload_fields and payload.installation_latitude != _to_float(job.installation_latitude):
        job.installation_latitude = payload.installation_latitude
        changed_fields.append("installation_latitude")

    if "installation_longitude" in payload_fields and payload.installation_longitude != _to_float(job.installation_longitude):
        job.installation_longitude = payload.installation_longitude
        changed_fields.append("installation_longitude")

    apply_text("installation_location", payload.installation_location)
    apply_text("asset_label", payload.asset_label)
    apply_text("asset_registration", payload.asset_registration)
    apply_text("notes", payload.notes)
    apply_text("completion_notes", payload.completion_notes)
    apply_text("decline_reason", payload.decline_reason)

    if "status" in payload_fields and payload.status is not None:
        next_status = payload.status
        if not is_admin and next_status not in {TechnicianJobStatus.assigned, TechnicianJobStatus.in_progress, TechnicianJobStatus.completed, TechnicianJobStatus.cancelled}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Technicians can only accept, decline, start, or complete assigned jobs",
            )
        if next_status == TechnicianJobStatus.assigned and not job.assigned_technician_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assign a technician before setting status to assigned",
            )
        if next_status == TechnicianJobStatus.assigned and not is_admin:
            if job.assigned_technician_id != actor.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the assigned technician can accept this job")
            job.accepted_at = datetime.now(timezone.utc)
            job.started_at = job.started_at or datetime.now(timezone.utc)
            job.cancelled_at = None
            job.declined_at = None
            job.status = TechnicianJobStatus.in_progress
            changed_fields.append("status:accepted")
        elif next_status == TechnicianJobStatus.in_progress:
            if job.assigned_technician_id and not is_admin and job.assigned_technician_id != actor.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the assigned technician can start this job")
            if not job.assigned_technician_id:
                job.assigned_technician_id = actor.id
            if not job.accepted_at:
                job.accepted_at = datetime.now(timezone.utc)
            if not job.started_at:
                job.started_at = datetime.now(timezone.utc)
            job.cancelled_at = None
            job.declined_at = None
            job.status = TechnicianJobStatus.in_progress
            changed_fields.append(f"status:{next_status.value}")
        elif next_status == TechnicianJobStatus.completed:
            if job.hardware and job.hardware.status in {HardwareStatus.FAULTY, HardwareStatus.RETIRED}:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot complete job with faulty or retired hardware",
                )
            if not job.assigned_technician_id:
                job.assigned_technician_id = actor.id
            if not job.accepted_at:
                job.accepted_at = datetime.now(timezone.utc)
            if not job.started_at:
                job.started_at = datetime.now(timezone.utc)
            install_time = payload.installed_at or job.installed_at or datetime.now(timezone.utc)
            reference = job.assignment_reference
            if job.hardware and (job.vehicle_id or job.asset_label or job.asset_registration):
                try:
                    reference = assign_hardware_to_vehicle(
                        db,
                        imei=job.hardware.imei,
                        vehicle_id=job.vehicle_id,
                        hub_id=job.hub_id,
                        hardware_type=job.hardware.hardware_type,
                        model=job.hardware.model,
                        assigned_by=actor.id,
                        requested_by=job.requested_by or actor.id,
                        technician=actor.name or actor.email,
                        installed_at=install_time,
                        installation_location=job.installation_location,
                        installation_latitude=_to_float(job.installation_latitude),
                        installation_longitude=_to_float(job.installation_longitude),
                        asset_label=job.asset_label,
                        asset_registration=job.asset_registration,
                        notes=job.completion_notes or job.notes,
                    )
                except ValueError as exc:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

            job.installed_at = install_time
            job.completed_at = datetime.now(timezone.utc)
            job.cancelled_at = None
            job.declined_at = None
            job.status = TechnicianJobStatus.completed
            job.assignment_reference = reference
            changed_fields.append(f"status:{next_status.value}")
        elif next_status == TechnicianJobStatus.cancelled:
            if not is_admin and job.assigned_technician_id != actor.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the assigned technician can decline this job")
            if not is_admin and not _clean_text(payload.decline_reason):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Decline reason is required")
            job.cancelled_at = datetime.now(timezone.utc)
            job.declined_at = datetime.now(timezone.utc)
            if not is_admin:
                job.decline_reason = _clean_text(payload.decline_reason)
            job.status = TechnicianJobStatus.cancelled
            changed_fields.append("status:declined" if not is_admin else f"status:{next_status.value}")
        else:
            if next_status == TechnicianJobStatus.pending and not is_admin:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can reset job to pending")
            job.status = next_status
            if next_status != TechnicianJobStatus.cancelled:
                job.cancelled_at = None
            changed_fields.append(f"status:{next_status.value}")

    if not changed_fields:
        return _serialize_job(job)

    db.add(job)
    db.commit()
    job = _load_job_or_404(job.id, db)

    append_admin_activity(
        db,
        module="technician-workflow",
        change="Technician job updated",
        details=f"{job.id} [{', '.join(changed_fields)}]",
        actor=actor,
        target_type="technician_job",
        target_id=str(job.id),
    )
    return _serialize_job(job)
