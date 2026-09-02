"""Hardware and device inventory routes."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import re
from typing import Iterable, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, Header, status
from sqlalchemy import and_, exists, func, not_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.auth import HUB_HEADER, HubAccessContext, require_hub_access, require_role
from app.core.database import get_db
from app.models.hub import Hub
from app.models.hardware import (
    HardwareAssignment,
    HardwareInventory,
    HardwareStatus,
    SimAssignment,
    SimInventory,
    SimStatus,
)
from app.models.hub_membership import HubMembership, HubMembershipStatus
from app.models.pairing import DevicePairing
from app.models.vehicle import Vehicle
from app.models.technician_job import TechnicianJob, TechnicianJobStatus
from app.models.user import User
from app.schemas.devices import (
    DeviceAssignment,
    DeviceAssignmentRequest,
    DeviceAssignmentHistoryItem,
    DeviceInventoryData,
    DeviceInventoryDetailResponse,
    DeviceInventoryItem,
    DeviceInventoryListResponse,
    DeviceInventorySummary,
    DeviceRecallRequest,
    DeviceReassignmentRequest,
    DeviceInventoryUpdateRequest,
    DevicePairingInfo,
    DeviceStatusUpdateRequest,
    DeviceIntakeRequest,
    PaginationMeta,
    SimAssignmentInfo,
    SimAssignmentHistoryItem,
    SimInventoryCreateRequest,
    SimInventoryData,
    SimInventoryDetailResponse,
    SimInventoryItem,
    SimInventoryListResponse,
    SimInventorySummary,
    SimInventoryUpdateRequest,
    SimAssignmentRequest,
    SimRecallRequest,
)
from app.services.hardware import (
    assign_hardware_to_vehicle,
    upsert_hardware,
    update_device_status as update_device_status_service,
)
from app.services.admin_activity import append_admin_activity
from app.models.user import UserRole

router = APIRouter(prefix="/devices", tags=["devices"])

READ_ROLES = (
    UserRole.admin,
    UserRole.technician,
    UserRole.client,
    UserRole.company,
)

WRITE_ROLES = (
    UserRole.admin,
)

ASSIGNMENT_ROLES = (
    UserRole.admin,
    UserRole.technician,
)

ASSET_PROFILE_BEGIN = "[asset-profile]"
ASSET_PROFILE_END = "[/asset-profile]"


def _is_global_admin(context: HubAccessContext) -> bool:
    return str(getattr(context.user.role, "value", context.user.role)).lower() == UserRole.admin.value


def _is_technician(context: HubAccessContext) -> bool:
    return str(getattr(context.user.role, "value", context.user.role)).lower() == UserRole.technician.value


def _is_internal_operator(user: User) -> bool:
    return str(getattr(user.role, "value", user.role)).lower() in {
        UserRole.admin.value,
        UserRole.technician.value,
    }


def _resolve_read_context(
    *,
    actor: User,
    hub_header: Optional[str],
    db: Session,
) -> HubAccessContext:
    if not hub_header and _is_internal_operator(actor):
        return HubAccessContext(user=actor, hub=None, membership=None)

    if not hub_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing {HUB_HEADER} header",
        )

    try:
        hub_uuid = UUID(str(hub_header))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid hub identifier '{hub_header}'",
        ) from exc

    hub = db.query(Hub).filter(Hub.id == hub_uuid).first()
    if not hub or hub.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hub not found")

    membership = (
        db.query(HubMembership)
        .filter(
            HubMembership.hub_id == hub_uuid,
            HubMembership.user_id == actor.id,
            HubMembership.status == HubMembershipStatus.active,
        )
        .first()
    )

    if membership is None and not _is_internal_operator(actor):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of the requested hub",
        )

    return HubAccessContext(user=actor, hub=hub, membership=membership)


def _scope_clause(context: HubAccessContext):
    if _is_global_admin(context) or (_is_technician(context) and context.hub is None):
        return None

    vehicle_ids_subquery = select(Vehicle.id).where(Vehicle.hub_id == context.hub.id)
    scoped_assignment = (
        exists()
        .where(
            HardwareAssignment.hardware_id == HardwareInventory.id,
            HardwareAssignment.is_active.is_(True),
            or_(
                HardwareAssignment.hub_id == context.hub.id,
                HardwareAssignment.vehicle_id.in_(vehicle_ids_subquery),
            ),
        )
        .correlate(HardwareInventory)
    )

    unassigned_inventory = and_(
        HardwareInventory.status == HardwareStatus.IN_STOCK,
        not_(
            exists()
            .where(
                HardwareAssignment.hardware_id == HardwareInventory.id,
                HardwareAssignment.is_active.is_(True),
            )
            .correlate(HardwareInventory)
        ),
    )

    return or_(scoped_assignment, unassigned_inventory)


def _parse_status(status_param: Optional[str]) -> Optional[HardwareStatus]:
    if not status_param:
        return None
    normalized = status_param.strip().lower()
    for member in HardwareStatus:
        if member.value == normalized:
            return member
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported hardware status '{status_param}'",
    )


def _clean_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_sim_identity(value: Optional[str], *, field: str) -> Optional[str]:
    cleaned = _clean_text(value)
    if not cleaned:
        return None
    compact = re.sub(r"\s+", "", cleaned)
    if field == "msisdn":
        return re.sub(r"[\s().-]+", "", compact)
    return compact


def _ensure_unique_sim_identity(
    *,
    db: Session,
    iccid: Optional[str] = None,
    msisdn: Optional[str] = None,
    imsi: Optional[str] = None,
    exclude_sim_id: Optional[int] = None,
) -> None:
    checks = [
        ("ICCID", SimInventory.iccid, iccid),
        ("SIM number", SimInventory.msisdn, msisdn),
        ("IMSI", SimInventory.apn, imsi),
    ]
    for label, column, value in checks:
        if not value:
            continue
        query = db.query(SimInventory).filter(column == value)
        if exclude_sim_id is not None:
            query = query.filter(SimInventory.id != exclude_sim_id)
        existing = query.first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{label} already exists on managed SIM {existing.iccid}",
            )


def _append_reason(existing: Optional[str], reason: Optional[str], *, prefix: str) -> Optional[str]:
    clean_reason = _clean_text(reason)
    if not clean_reason:
        return existing
    note = f"{prefix}: {clean_reason}"
    if not existing:
        return note
    return f"{existing.rstrip()}\n{note}"


def _validate_technician_job_access(
    *,
    db: Session,
    context: HubAccessContext,
    source_job_id: Optional[str],
    target_hub_id: Optional[UUID],
) -> Optional[TechnicianJob]:
    if not _is_technician(context):
        return None
    if not source_job_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Technician actions must be linked to an active job card",
        )
    try:
        source_job_uuid = UUID(str(source_job_id))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid source job ID") from exc

    source_job = db.query(TechnicianJob).filter(TechnicianJob.id == source_job_uuid).first()
    if not source_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Technician job not found")
    if source_job.assigned_technician_id != context.user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assigned technician can manage hardware for this job",
        )
    if source_job.status not in {TechnicianJobStatus.assigned, TechnicianJobStatus.in_progress}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hardware workflow changes are only allowed while the job is active",
        )
    if target_hub_id and source_job.hub_id != target_hub_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Technician hardware changes must stay within the assigned job hub",
        )
    return source_job


def _combine_assignment_notes(
    *,
    free_notes: Optional[str],
    asset_type: Optional[str],
    asset_name: Optional[str],
    vehicle_make: Optional[str],
    vehicle_model: Optional[str],
    vehicle_year: Optional[str],
    engine_capacity: Optional[str],
    vin: Optional[str],
) -> Optional[str]:
    profile_lines: list[str] = []
    fields = [
        ("type", asset_type),
        ("name", asset_name),
        ("make", vehicle_make),
        ("model", vehicle_model),
        ("year", vehicle_year),
        ("engine_capacity", engine_capacity),
        ("vin", vin),
    ]
    for key, raw_value in fields:
        value = _clean_text(raw_value)
        if value:
            profile_lines.append(f"{key}: {value}")

    sections: list[str] = []
    if profile_lines:
        sections.append("\n".join([ASSET_PROFILE_BEGIN, *profile_lines, ASSET_PROFILE_END]))
    clean_notes = _clean_text(free_notes)
    if clean_notes:
        sections.append(clean_notes)
    combined = "\n\n".join(sections).strip()
    return combined or None


def _active_assignment(assignments: Iterable[HardwareAssignment]) -> Optional[HardwareAssignment]:
    for assignment in assignments:
        if assignment.is_active:
            return assignment
    return None


def _active_sim_assignment(assignments: Iterable[SimAssignment]) -> Optional[SimAssignment]:
    for assignment in assignments:
        if assignment.is_active:
            return assignment
    return None


def _serialize_sim_assignment(
    assignment: SimAssignment,
) -> SimAssignmentHistoryItem:
    hardware = assignment.hardware
    vehicle = assignment.vehicle
    hub = assignment.hub or (vehicle.hub if vehicle else None)
    target = "vehicle" if assignment.vehicle_id else ("hub" if assignment.hub_id else "hardware")
    return SimAssignmentHistoryItem(
        id=assignment.id,
        target=target,
        hardware_id=assignment.hardware_id,
        hardware_imei=hardware.imei if hardware else None,
        hub_id=hub.id if hub else assignment.hub_id,
        hub_name=hub.name if hub else (assignment.hub.name if assignment.hub else None),
        vehicle_id=assignment.vehicle_id,
        vehicle_label=(
            vehicle.license_plate
            if vehicle and vehicle.license_plate
            else (vehicle.vin if vehicle and vehicle.vin else vehicle.model if vehicle else None)
        ),
        technician=assignment.assigned_user.name if assignment.assigned_user else None,
        assigned_at=assignment.assigned_at,
        unassigned_at=assignment.unassigned_at,
        notes=assignment.notes,
        is_active=assignment.is_active,
    )


def _serialize_sim(
    sim: SimInventory,
) -> SimInventoryItem:
    history = sorted(
        sim.assignments or [],
        key=lambda assignment: assignment.assigned_at or assignment.created_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    active_assignment = _active_sim_assignment(history)
    assignment_payload: Optional[SimAssignmentInfo] = None
    if active_assignment:
        hardware = active_assignment.hardware
        vehicle = active_assignment.vehicle
        hub = active_assignment.hub or (vehicle.hub if vehicle else None)
        assignment_payload = SimAssignmentInfo(
            target="vehicle" if active_assignment.vehicle_id else ("hub" if active_assignment.hub_id else "hardware"),
            hardware_id=active_assignment.hardware_id,
            hardware_imei=hardware.imei if hardware else None,
            hub_id=hub.id if hub else active_assignment.hub_id,
            hub_name=hub.name if hub else (active_assignment.hub.name if active_assignment.hub else None),
            vehicle_id=active_assignment.vehicle_id,
            vehicle_label=(
                vehicle.license_plate
                if vehicle and vehicle.license_plate
                else (vehicle.vin if vehicle and vehicle.vin else vehicle.model if vehicle else None)
            ),
            assigned_at=active_assignment.assigned_at,
            technician=active_assignment.assigned_user.name if active_assignment.assigned_user else None,
            notes=active_assignment.notes,
        )
    return SimInventoryItem(
        id=sim.id,
        iccid=sim.iccid,
        msisdn=sim.msisdn,
        carrier=sim.carrier,
        imsi=sim.apn,
        roaming_enabled=bool(sim.roaming_enabled),
        roaming_regions=sim.roaming_regions,
        status=sim.status,
        notes=sim.notes,
        created_at=sim.created_at,
        updated_at=sim.updated_at,
        assignment=assignment_payload,
        assignment_history=[_serialize_sim_assignment(item) for item in history],
    )


def _assign_sim_to_hardware(
    *,
    db: Session,
    sim: SimInventory,
    hardware: HardwareInventory,
    assigned_by,
    hub_id: Optional[UUID],
    vehicle_id: Optional[UUID],
    notes: Optional[str] = None,
) -> None:
    current_assignment = _active_sim_assignment(sim.assignments or [])
    if (
        current_assignment
        and current_assignment.hardware_id == hardware.id
        and current_assignment.vehicle_id == vehicle_id
        and current_assignment.hub_id == hub_id
    ):
        if _clean_text(notes):
            current_assignment.notes = _append_reason(current_assignment.notes, notes, prefix="Assignment notes")
            db.add(current_assignment)
            db.flush()
        return

    if current_assignment:
        current_assignment.is_active = False
        current_assignment.unassigned_at = datetime.now(timezone.utc)
        db.add(current_assignment)

    assignment = SimAssignment(
        sim_id=sim.id,
        hardware_id=hardware.id,
        hub_id=hub_id,
        vehicle_id=vehicle_id,
        assigned_by=assigned_by,
        notes=_clean_text(notes),
        is_active=True,
    )
    sim.status = SimStatus.ASSIGNED
    db.add(sim)
    db.add(assignment)
    db.flush()


def _recall_sim_assignment(
    *,
    db: Session,
    assignment: SimAssignment,
    status_value: SimStatus,
    reason: str,
    notes: Optional[str] = None,
) -> None:
    assignment.notes = _append_reason(assignment.notes, reason, prefix="Recalled")
    if _clean_text(notes):
        assignment.notes = _append_reason(assignment.notes, notes, prefix="Recall notes")
    assignment.is_active = False
    assignment.unassigned_at = datetime.now(timezone.utc)
    if assignment.sim:
        assignment.sim.status = status_value
        db.add(assignment.sim)
    db.add(assignment)
    db.flush()


def _sync_active_sim_assignment(
    *,
    db: Session,
    hardware: HardwareInventory,
    hub_id: Optional[UUID],
    vehicle_id: Optional[UUID],
) -> None:
    active_sim_assignment = _active_sim_assignment(hardware.sim_assignments or [])
    if not active_sim_assignment:
        return
    active_sim_assignment.hub_id = hub_id
    active_sim_assignment.vehicle_id = vehicle_id
    db.add(active_sim_assignment)
    db.flush()


def _latest_pairing(pairings: Iterable[DevicePairing]) -> Optional[DevicePairing]:
    latest: Optional[DevicePairing] = None
    for pairing in pairings:
        if latest is None:
            latest = pairing
            continue
        latest_ts = latest.approved_at or latest.created_at
        candidate_ts = pairing.approved_at or pairing.created_at
        if candidate_ts and (not latest_ts or candidate_ts >= latest_ts):
            latest = pairing
    return latest


def _serialize_device(
    hardware: HardwareInventory,
) -> DeviceInventoryItem:
    assignment_payload: Optional[DeviceAssignment] = None
    assignment_history_payload: list[DeviceAssignmentHistoryItem] = []
    pairing_payload: Optional[DevicePairingInfo] = None
    sim_payload: Optional[SimInventoryItem] = None

    assignment_records = sorted(
        hardware.assignments or [],
        key=lambda assignment: assignment.assigned_at or assignment.created_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    sim_records = sorted(
        hardware.sim_assignments or [],
        key=lambda assignment: assignment.assigned_at or assignment.created_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    active_assignment = _active_assignment(assignment_records)
    active_sim_assignment = _active_sim_assignment(sim_records)
    for assignment in assignment_records:
        vehicle = assignment.vehicle
        hub = assignment.hub or (vehicle.hub if vehicle else None)
        target = "vehicle" if assignment.vehicle_id else ("hub" if assignment.hub_id else "inventory")
        sim_for_assignment = next(
            (
                sim_assignment.sim
                for sim_assignment in sim_records
                if sim_assignment.assigned_at
                and assignment.assigned_at
                and abs((sim_assignment.assigned_at - assignment.assigned_at).total_seconds()) < 1
                and sim_assignment.hardware_id == assignment.hardware_id
            ),
            active_sim_assignment.sim if active_sim_assignment and active_sim_assignment.hardware_id == assignment.hardware_id else None,
        )
        assignment_history_payload.append(
            DeviceAssignmentHistoryItem(
                id=assignment.id,
                target=target,
                hub_id=hub.id if hub else assignment.hub_id,
                hub_name=hub.name if hub else (assignment.hub.name if assignment.hub else None),
                vehicle_id=assignment.vehicle_id,
                vehicle_label=(
                    vehicle.license_plate
                    if vehicle and vehicle.license_plate
                    else (vehicle.vin if vehicle and vehicle.vin else vehicle.model if vehicle else None)
                ),
                technician=assignment.assigned_user.name if assignment.assigned_user else None,
                assigned_at=assignment.assigned_at,
                installed_at=assignment.installed_at,
                unassigned_at=assignment.unassigned_at,
                installation_location=assignment.installation_location,
                installation_latitude=float(assignment.installation_latitude) if assignment.installation_latitude is not None else None,
                installation_longitude=float(assignment.installation_longitude) if assignment.installation_longitude is not None else None,
                asset_label=assignment.asset_label,
                asset_registration=assignment.asset_registration,
                notes=assignment.notes,
                is_active=assignment.is_active,
                sim_id=sim_for_assignment.id if sim_for_assignment else None,
                sim_iccid=sim_for_assignment.iccid if sim_for_assignment else None,
                sim_msisdn=sim_for_assignment.msisdn if sim_for_assignment else None,
                sim_carrier=sim_for_assignment.carrier if sim_for_assignment else None,
                sim_roaming_enabled=bool(sim_for_assignment.roaming_enabled) if sim_for_assignment else None,
            )
        )

    if active_assignment:
        vehicle = active_assignment.vehicle
        hub = active_assignment.hub or (vehicle.hub if vehicle else None)
        target = "vehicle" if active_assignment.vehicle_id else ("hub" if active_assignment.hub_id else "inventory")
        assignment_payload = DeviceAssignment(
            target=target,
            hub_id=hub.id if hub else active_assignment.hub_id,
            hub_name=hub.name if hub else (active_assignment.hub.name if active_assignment.hub else None),
            vehicle_id=active_assignment.vehicle_id,
            vehicle_label=(
                vehicle.license_plate
                if vehicle and vehicle.license_plate
                else (vehicle.vin if vehicle and vehicle.vin else vehicle.model if vehicle else None)
            ),
            technician=active_assignment.assigned_user.name if active_assignment.assigned_user else None,
            assigned_at=active_assignment.assigned_at,
            installed_at=active_assignment.installed_at,
            installation_location=active_assignment.installation_location,
            installation_latitude=float(active_assignment.installation_latitude) if active_assignment.installation_latitude is not None else None,
            installation_longitude=float(active_assignment.installation_longitude) if active_assignment.installation_longitude is not None else None,
            asset_label=active_assignment.asset_label,
            asset_registration=active_assignment.asset_registration,
            notes=active_assignment.notes,
            sim_id=active_sim_assignment.sim.id if active_sim_assignment and active_sim_assignment.sim else None,
            sim_iccid=active_sim_assignment.sim.iccid if active_sim_assignment and active_sim_assignment.sim else None,
            sim_msisdn=active_sim_assignment.sim.msisdn if active_sim_assignment and active_sim_assignment.sim else None,
            sim_carrier=active_sim_assignment.sim.carrier if active_sim_assignment and active_sim_assignment.sim else None,
            sim_roaming_enabled=bool(active_sim_assignment.sim.roaming_enabled) if active_sim_assignment and active_sim_assignment.sim else None,
        )

    if active_sim_assignment and active_sim_assignment.sim:
        sim_payload = _serialize_sim(active_sim_assignment.sim)

    latest_pairing = _latest_pairing(hardware.pairings or [])
    if latest_pairing:
        pairing_payload = DevicePairingInfo(
            status=latest_pairing.status.value if latest_pairing.status else None,
            requested_by=(
                latest_pairing.requester.name
                if latest_pairing.requester and latest_pairing.requester.name
                else latest_pairing.requester.email if latest_pairing.requester else None
            ),
            approved_by=(
                latest_pairing.approver.name
                if latest_pairing.approver and latest_pairing.approver.name
                else latest_pairing.approver.email if latest_pairing.approver else None
            ),
            approved_at=latest_pairing.approved_at,
            notes=latest_pairing.notes,
        )

    purchase_cost = None
    if hardware.purchase_cost is not None:
        purchase_cost = float(hardware.purchase_cost) if isinstance(hardware.purchase_cost, Decimal) else hardware.purchase_cost

    return DeviceInventoryItem(
        id=hardware.id,
        imei=hardware.imei,
        serial_number=hardware.serial_number,
        hardware_type=hardware.hardware_type,
        model=hardware.model,
        manufacturer=hardware.manufacturer,
        firmware_version=hardware.firmware_version,
        status=hardware.status,
        notes=hardware.notes,
        purchase_date=hardware.purchase_date,
        purchase_cost=purchase_cost,
        created_at=hardware.created_at,
        updated_at=hardware.updated_at,
        last_seen_at=hardware.updated_at,
        assignment=assignment_payload,
        assignment_history=assignment_history_payload,
        sim=sim_payload,
        pairing=pairing_payload,
    )


def _base_filters(context: HubAccessContext, search: Optional[str]):
    filters = []
    scope_expression = _scope_clause(context)
    if scope_expression is not None:
        filters.append(scope_expression)

    if search:
        like_pattern = f"%{search.strip().lower()}%"
        filters.append(
            or_(
                func.lower(HardwareInventory.imei).like(like_pattern),
                func.lower(HardwareInventory.serial_number).like(like_pattern),
                func.lower(HardwareInventory.model).like(like_pattern),
                func.lower(HardwareInventory.notes).like(like_pattern),
            )
        )
    return filters


def _load_hardware_or_404(
    hardware_id: int,
    context: HubAccessContext,
    db: Session,
    *,
    with_relationships: bool = True,
) -> HardwareInventory:
    query = db.query(HardwareInventory)
    if with_relationships:
        query = query.options(
            joinedload(HardwareInventory.assignments)
            .joinedload(HardwareAssignment.vehicle)
            .joinedload(Vehicle.hub),
            joinedload(HardwareInventory.assignments).joinedload(HardwareAssignment.hub),
            joinedload(HardwareInventory.assignments).joinedload(HardwareAssignment.assigned_user),
            joinedload(HardwareInventory.sim_assignments).joinedload(SimAssignment.sim),
            joinedload(HardwareInventory.sim_assignments).joinedload(SimAssignment.vehicle).joinedload(Vehicle.hub),
            joinedload(HardwareInventory.sim_assignments).joinedload(SimAssignment.hub),
            joinedload(HardwareInventory.sim_assignments).joinedload(SimAssignment.assigned_user),
            joinedload(HardwareInventory.pairings).joinedload(DevicePairing.requester),
            joinedload(HardwareInventory.pairings).joinedload(DevicePairing.approver),
        )

    filters = _base_filters(context, search=None)
    filters.append(HardwareInventory.id == hardware_id)
    hardware = query.filter(*filters).first()
    if not hardware:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hardware not found")
    return hardware


def _sim_scope_clause(context: HubAccessContext):
    if _is_global_admin(context) or (_is_technician(context) and context.hub is None):
        return None

    vehicle_ids_subquery = select(Vehicle.id).where(Vehicle.hub_id == context.hub.id)
    scoped_assignment = (
        exists()
        .where(
            SimAssignment.sim_id == SimInventory.id,
            SimAssignment.is_active.is_(True),
            or_(
                SimAssignment.hub_id == context.hub.id,
                SimAssignment.vehicle_id.in_(vehicle_ids_subquery),
            ),
        )
        .correlate(SimInventory)
    )

    unassigned_inventory = and_(
        SimInventory.status == SimStatus.IN_STOCK,
        not_(
            exists()
            .where(
                SimAssignment.sim_id == SimInventory.id,
                SimAssignment.is_active.is_(True),
            )
            .correlate(SimInventory)
        ),
    )
    return or_(scoped_assignment, unassigned_inventory)


def _load_sim_or_404(
    sim_id: int,
    context: HubAccessContext,
    db: Session,
    *,
    with_relationships: bool = True,
) -> SimInventory:
    query = db.query(SimInventory)
    if with_relationships:
        query = query.options(
            joinedload(SimInventory.assignments).joinedload(SimAssignment.hardware),
            joinedload(SimInventory.assignments).joinedload(SimAssignment.vehicle).joinedload(Vehicle.hub),
            joinedload(SimInventory.assignments).joinedload(SimAssignment.hub),
            joinedload(SimInventory.assignments).joinedload(SimAssignment.assigned_user),
        )
    scope_expression = _sim_scope_clause(context)
    if scope_expression is not None:
        query = query.filter(scope_expression)
    sim = query.filter(SimInventory.id == sim_id).first()
    if not sim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SIM not found")
    return sim


@router.post("/", response_model=DeviceInventoryDetailResponse, status_code=status.HTTP_201_CREATED)
async def intake_device(
    payload: DeviceIntakeRequest,
    context: HubAccessContext = Depends(require_hub_access(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    """Create or update a hardware record during intake."""

    hardware = upsert_hardware(
        db,
        imei=payload.imei,
        hardware_type=payload.hardware_type,
        model=payload.model,
        manufacturer=payload.manufacturer,
        firmware_version=payload.firmware_version,
        serial_number=payload.serial_number,
        notes=payload.notes,
    )

    if hardware.status is None:
        hardware.status = HardwareStatus.IN_STOCK
    if payload.purchase_date:
        hardware.purchase_date = payload.purchase_date

    db.commit()
    db.refresh(hardware)
    append_admin_activity(
        db,
        module="assets",
        change="Device intake",
        details=f"IMEI {hardware.imei} added/updated in inventory",
        actor=context.user,
        target_type="device",
        target_id=str(hardware.id),
    )

    hydrated = _load_hardware_or_404(hardware.id, context, db)
    return DeviceInventoryDetailResponse(data=_serialize_device(hydrated))


@router.post("/sims", response_model=SimInventoryDetailResponse, status_code=status.HTTP_201_CREATED)
async def intake_sim(
    payload: SimInventoryCreateRequest,
    context: HubAccessContext = Depends(require_hub_access(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    """Create a new managed SIM card inventory record."""

    normalized_iccid = _normalize_sim_identity(payload.iccid, field="iccid")
    normalized_msisdn = _normalize_sim_identity(payload.msisdn, field="msisdn")
    normalized_imsi = _normalize_sim_identity(payload.imsi, field="imsi")
    if not normalized_iccid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ICCID is required")

    _ensure_unique_sim_identity(
        db=db,
        iccid=normalized_iccid,
        msisdn=normalized_msisdn,
        imsi=normalized_imsi,
    )

    sim = SimInventory(
        iccid=normalized_iccid,
        msisdn=normalized_msisdn,
        carrier=_clean_text(payload.carrier) or "Econet",
        apn=normalized_imsi,
        roaming_enabled=bool(payload.roaming_enabled),
        roaming_regions=_clean_text(payload.roaming_regions),
        status=SimStatus.IN_STOCK,
        notes=_clean_text(payload.notes),
    )
    db.add(sim)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SIM ICCID or MSISDN already exists")
    db.refresh(sim)
    append_admin_activity(
        db,
        module="assets",
        change="SIM intake",
        details=f"SIM {sim.iccid} added to inventory",
        actor=context.user,
        target_type="sim",
        target_id=str(sim.id),
    )
    hydrated = _load_sim_or_404(sim.id, context, db)
    return SimInventoryDetailResponse(data=_serialize_sim(hydrated))


@router.get("/sims", response_model=SimInventoryListResponse)
async def list_sims(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by SIM lifecycle status"),
    search: Optional[str] = Query(None, min_length=2, description="Search ICCID, MSISDN, carrier, or notes"),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=200),
    hub_header: Optional[str] = Header(None, alias=HUB_HEADER),
    actor: User = Depends(require_role(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    """List SIM inventory records."""
    context = _resolve_read_context(actor=actor, hub_header=hub_header, db=db)

    status_enum = None
    if status_filter:
        normalized = status_filter.strip().lower()
        for member in SimStatus:
            if member.value == normalized:
                status_enum = member
                break
        if status_enum is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported sim status '{status_filter}'")

    scope_expression = _sim_scope_clause(context)
    query = db.query(SimInventory).options(
        joinedload(SimInventory.assignments).joinedload(SimAssignment.hardware),
        joinedload(SimInventory.assignments).joinedload(SimAssignment.vehicle).joinedload(Vehicle.hub),
        joinedload(SimInventory.assignments).joinedload(SimAssignment.hub),
        joinedload(SimInventory.assignments).joinedload(SimAssignment.assigned_user),
    )
    if scope_expression is not None:
        query = query.filter(scope_expression)
    if search:
        like = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                func.lower(SimInventory.iccid).like(like),
                func.lower(func.coalesce(SimInventory.msisdn, "")).like(like),
                func.lower(func.coalesce(SimInventory.carrier, "")).like(like),
                func.lower(func.coalesce(SimInventory.roaming_regions, "")).like(like),
                func.lower(func.coalesce(SimInventory.notes, "")).like(like),
            )
        )

    total = query.count()
    if status_enum:
        query = query.filter(SimInventory.status == status_enum)
    filtered_total = query.count()
    items = (
        query.order_by(SimInventory.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    status_counts: dict[str, int] = {member.value: 0 for member in SimStatus}
    counts_query = db.query(SimInventory.status, func.count(SimInventory.id))
    if scope_expression is not None:
        counts_query = counts_query.filter(scope_expression)
    for row_status, count in counts_query.group_by(SimInventory.status).all():
        key = row_status.value if isinstance(row_status, SimStatus) else str(row_status)
        status_counts[key] = count

    return SimInventoryListResponse(
        data=SimInventoryData(items=[_serialize_sim(item) for item in items]),
        summary=SimInventorySummary(
            total=total,
            visible=len(items),
            updated_at=datetime.now(timezone.utc),
            status_counts=status_counts,
        ),
        meta=PaginationMeta(page=page, per_page=limit, total=filtered_total),
    )


@router.get("/sims/{sim_id}", response_model=SimInventoryDetailResponse)
async def get_sim(
    sim_id: int,
    hub_header: Optional[str] = Header(None, alias=HUB_HEADER),
    actor: User = Depends(require_role(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    context = _resolve_read_context(actor=actor, hub_header=hub_header, db=db)
    sim = _load_sim_or_404(sim_id, context, db)
    return SimInventoryDetailResponse(data=_serialize_sim(sim))


@router.patch("/sims/{sim_id}", response_model=SimInventoryDetailResponse)
async def update_sim(
    sim_id: int,
    payload: SimInventoryUpdateRequest,
    context: HubAccessContext = Depends(require_hub_access(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    sim = _load_sim_or_404(sim_id, context, db, with_relationships=False)
    next_msisdn = _normalize_sim_identity(
        payload.msisdn if "msisdn" in payload.model_fields_set else sim.msisdn,
        field="msisdn",
    )
    next_imsi = _normalize_sim_identity(
        payload.imsi if "imsi" in payload.model_fields_set else sim.apn,
        field="imsi",
    )
    _ensure_unique_sim_identity(
        db=db,
        msisdn=next_msisdn,
        imsi=next_imsi,
        exclude_sim_id=sim.id,
    )
    if "msisdn" in payload.model_fields_set:
        sim.msisdn = next_msisdn
    if "carrier" in payload.model_fields_set:
        sim.carrier = _clean_text(payload.carrier) or "Econet"
    if "imsi" in payload.model_fields_set:
        sim.apn = next_imsi
    if "roaming_enabled" in payload.model_fields_set and payload.roaming_enabled is not None:
        sim.roaming_enabled = bool(payload.roaming_enabled)
    if "roaming_regions" in payload.model_fields_set:
        sim.roaming_regions = _clean_text(payload.roaming_regions)
    if "status" in payload.model_fields_set and payload.status is not None:
        sim.status = payload.status
    if "notes" in payload.model_fields_set:
        sim.notes = _clean_text(payload.notes)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SIM number or IMSI already exists")
    append_admin_activity(
        db,
        module="assets",
        change="SIM updated",
        details=f"SIM {sim.iccid} metadata edited",
        actor=context.user,
        target_type="sim",
        target_id=str(sim.id),
    )
    hydrated = _load_sim_or_404(sim_id, context, db)
    return SimInventoryDetailResponse(data=_serialize_sim(hydrated))


@router.delete("/sims/{sim_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sim(
    sim_id: int,
    context: HubAccessContext = Depends(require_hub_access(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    sim = _load_sim_or_404(sim_id, context, db)
    active_assignment = _active_sim_assignment(sim.assignments or [])
    if active_assignment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Recall the active SIM assignment before deleting this managed SIM.",
        )

    iccid = sim.iccid
    target_id = str(sim.id)
    db.delete(sim)
    db.commit()
    append_admin_activity(
        db,
        module="assets",
        change="SIM deleted",
        details=f"SIM {iccid} removed from inventory",
        actor=context.user,
        target_type="sim",
        target_id=target_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/sims/{sim_id}/assign", response_model=SimInventoryDetailResponse)
async def assign_sim(
    sim_id: int,
    payload: SimAssignmentRequest,
    context: HubAccessContext = Depends(require_hub_access(UserRole.admin, UserRole.technician)),
    db: Session = Depends(get_db),
):
    sim = _load_sim_or_404(sim_id, context, db)
    hardware = _load_hardware_or_404(payload.hardware_id, context, db, with_relationships=True)
    current_hardware_assignment = _active_assignment(hardware.assignments or [])
    hub_id = payload.hub_id or (current_hardware_assignment.hub_id if current_hardware_assignment else None)
    vehicle_id = payload.vehicle_id or (current_hardware_assignment.vehicle_id if current_hardware_assignment else None)
    _validate_technician_job_access(
        db=db,
        context=context,
        source_job_id=payload.source_job_id,
        target_hub_id=hub_id,
    )
    if sim.status not in {SimStatus.IN_STOCK, SimStatus.SUSPENDED, SimStatus.ASSIGNED}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SIM is not available for assignment")
    _assign_sim_to_hardware(
        db=db,
        sim=sim,
        hardware=hardware,
        assigned_by=context.user.id,
        hub_id=hub_id,
        vehicle_id=vehicle_id,
        notes=payload.notes,
    )
    append_admin_activity(
        db,
        module="assets",
        change="SIM assigned",
        details=f"SIM {sim.iccid} assigned to IMEI {hardware.imei}",
        actor=context.user,
        target_type="sim",
        target_id=str(sim.id),
    )
    hydrated = _load_sim_or_404(sim_id, context, db)
    return SimInventoryDetailResponse(data=_serialize_sim(hydrated))


@router.post("/sims/{sim_id}/recall", response_model=SimInventoryDetailResponse)
async def recall_sim(
    sim_id: int,
    payload: SimRecallRequest,
    context: HubAccessContext = Depends(require_hub_access(UserRole.admin, UserRole.technician)),
    db: Session = Depends(get_db),
):
    sim = _load_sim_or_404(sim_id, context, db)
    assignment = _active_sim_assignment(sim.assignments or [])
    if not assignment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected SIM has no active assignment")
    hub_id = assignment.hub_id or (assignment.vehicle.hub_id if assignment.vehicle else None)
    _validate_technician_job_access(
        db=db,
        context=context,
        source_job_id=payload.source_job_id,
        target_hub_id=hub_id,
    )
    reason = _clean_text(payload.reason)
    if not reason:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A recall reason is required")
    if payload.status not in {SimStatus.IN_STOCK, SimStatus.ASSIGNED, SimStatus.SUSPENDED, SimStatus.FAULTY, SimStatus.RETIRED}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid SIM recall status")
    _recall_sim_assignment(db=db, assignment=assignment, status_value=payload.status, reason=reason, notes=payload.notes)
    append_admin_activity(
        db,
        module="assets",
        change="SIM recalled",
        details=f"SIM {sim.iccid} recalled as {payload.status.value}",
        actor=context.user,
        target_type="sim",
        target_id=str(sim.id),
    )
    hydrated = _load_sim_or_404(sim_id, context, db)
    return SimInventoryDetailResponse(data=_serialize_sim(hydrated))


@router.get("/", response_model=DeviceInventoryListResponse)
async def list_devices(  # noqa: D401 - FastAPI generates docs
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by lifecycle status"),
    sim_filter: Optional[str] = Query(None, alias="simFilter", description="Filter by active SIM state"),
    search: Optional[str] = Query(None, min_length=2, description="Search IMEI, serial, model, or notes"),
    hub_id_filter: Optional[UUID] = Query(None, alias="hubId", description="Filter deployed hardware to a specific hub"),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=200),
    hub_header: Optional[str] = Header(None, alias=HUB_HEADER),
    actor: User = Depends(require_role(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    """List hardware inventory records, scoped to the caller's hub."""
    context = _resolve_read_context(actor=actor, hub_header=hub_header, db=db)

    status_enum = _parse_status(status_filter)
    base_filters = _base_filters(context, search)
    if hub_id_filter is not None:
        base_filters.append(
            exists()
            .where(
                HardwareAssignment.hardware_id == HardwareInventory.id,
                HardwareAssignment.is_active.is_(True),
                or_(
                    HardwareAssignment.hub_id == hub_id_filter,
                    HardwareAssignment.vehicle_id.in_(select(Vehicle.id).where(Vehicle.hub_id == hub_id_filter)),
                ),
            )
            .correlate(HardwareInventory)
        )

    status_counts: dict[str, int] = {member.value: 0 for member in HardwareStatus}
    status_rows = (
        db.query(HardwareInventory.status, func.count(HardwareInventory.id))
        .filter(*base_filters)
        .group_by(HardwareInventory.status)
        .all()
    )
    for row_status, count in status_rows:
        key = row_status.value if isinstance(row_status, HardwareStatus) else str(row_status)
        status_counts[key] = count

    total_query = db.query(func.count(HardwareInventory.id)).filter(*base_filters)
    total = total_query.scalar() or 0

    normalized_sim_filter = sim_filter.strip().lower() if sim_filter else None
    sim_condition = None
    if normalized_sim_filter == "with_sim":
        sim_condition = exists().where(
            SimAssignment.hardware_id == HardwareInventory.id,
            SimAssignment.is_active.is_(True),
        ).correlate(HardwareInventory)
    elif normalized_sim_filter == "without_sim":
        sim_condition = not_(
            exists().where(
                SimAssignment.hardware_id == HardwareInventory.id,
                SimAssignment.is_active.is_(True),
            ).correlate(HardwareInventory)
        )
    elif normalized_sim_filter == "roaming":
        sim_condition = exists().where(
            SimAssignment.hardware_id == HardwareInventory.id,
            SimAssignment.is_active.is_(True),
            SimAssignment.sim_id == SimInventory.id,
            SimInventory.roaming_enabled.is_(True),
        ).correlate(HardwareInventory, SimInventory)
    elif normalized_sim_filter == "attention":
        sim_condition = exists().where(
            SimAssignment.hardware_id == HardwareInventory.id,
            SimAssignment.is_active.is_(True),
            SimAssignment.sim_id == SimInventory.id,
            SimInventory.status.in_([SimStatus.SUSPENDED, SimStatus.FAULTY]),
        ).correlate(HardwareInventory, SimInventory)
    elif normalized_sim_filter not in {None, "all"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported sim filter '{sim_filter}'")

    filtered_query = db.query(HardwareInventory).options(
        joinedload(HardwareInventory.assignments)
        .joinedload(HardwareAssignment.vehicle)
        .joinedload(Vehicle.hub),
        joinedload(HardwareInventory.assignments).joinedload(HardwareAssignment.hub),
        joinedload(HardwareInventory.assignments).joinedload(HardwareAssignment.assigned_user),
        joinedload(HardwareInventory.pairings).joinedload(DevicePairing.requester),
        joinedload(HardwareInventory.pairings).joinedload(DevicePairing.approver),
    ).filter(*base_filters)

    if status_enum:
        filtered_query = filtered_query.filter(HardwareInventory.status == status_enum)
    if sim_condition is not None:
        filtered_query = filtered_query.filter(sim_condition)

    filtered_total_query = db.query(func.count(HardwareInventory.id)).filter(*base_filters)
    if status_enum:
        filtered_total_query = filtered_total_query.filter(HardwareInventory.status == status_enum)
    if sim_condition is not None:
        filtered_total_query = filtered_total_query.filter(sim_condition)
    filtered_total = filtered_total_query.scalar() or 0

    offset = (page - 1) * limit
    records = (
        filtered_query
        .order_by(HardwareInventory.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = [_serialize_device(record) for record in records]
    summary = DeviceInventorySummary(
        total=total,
        visible=len(items),
        updated_at=datetime.now(timezone.utc),
        status_counts=status_counts,
    )
    meta = PaginationMeta(page=page, per_page=limit, total=filtered_total)
    return DeviceInventoryListResponse(data=DeviceInventoryData(items=items), summary=summary, meta=meta)


@router.get("/{hardware_id}", response_model=DeviceInventoryDetailResponse)
async def get_device(
    hardware_id: int,
    context: HubAccessContext = Depends(require_hub_access(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    """Fetch a single hardware record."""

    hardware = _load_hardware_or_404(hardware_id, context, db)
    return DeviceInventoryDetailResponse(data=_serialize_device(hardware))


@router.patch("/{hardware_id}/status", response_model=DeviceInventoryDetailResponse)
async def update_device_status(
    hardware_id: int,
    payload: DeviceStatusUpdateRequest,
    context: HubAccessContext = Depends(require_hub_access(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    """Update the lifecycle status for a hardware record."""

    hardware = _load_hardware_or_404(hardware_id, context, db, with_relationships=False)
    update_device_status_service(db, imei=hardware.imei, status=payload.status, notes=payload.notes)
    append_admin_activity(
        db,
        module="assets",
        change="Device status updated",
        details=f"IMEI {hardware.imei} set to {payload.status.value}",
        actor=context.user,
        target_type="device",
        target_id=str(hardware.id),
    )
    # Reload with relationships to return an updated snapshot
    refreshed = _load_hardware_or_404(hardware_id, context, db)
    return DeviceInventoryDetailResponse(data=_serialize_device(refreshed))


@router.patch("/{hardware_id}", response_model=DeviceInventoryDetailResponse)
async def update_device_details(
    hardware_id: int,
    payload: DeviceInventoryUpdateRequest,
    context: HubAccessContext = Depends(require_hub_access(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    """Persist firmware, notes, or status edits for a hardware record."""

    hardware = _load_hardware_or_404(hardware_id, context, db, with_relationships=False)
    status_changed = False

    mutated = False

    def apply_text_field(field_name: str, value: Optional[str]):
        nonlocal mutated
        if field_name not in payload.model_fields_set:
            return
        normalized = value.strip() if value else ""
        setattr(hardware, field_name, normalized or None)
        mutated = True

    if payload.status is not None:
        update_device_status_service(db, imei=hardware.imei, status=payload.status)
        status_changed = True
        hardware = _load_hardware_or_404(hardware_id, context, db, with_relationships=False)

    apply_text_field("firmware_version", payload.firmware_version)
    apply_text_field("notes", payload.notes)
    apply_text_field("hardware_type", payload.hardware_type)
    apply_text_field("model", payload.model)
    apply_text_field("manufacturer", payload.manufacturer)
    apply_text_field("serial_number", payload.serial_number)

    if "purchase_date" in payload.model_fields_set:
        hardware.purchase_date = payload.purchase_date
        mutated = True

    if mutated:
        db.commit()
        append_admin_activity(
            db,
            module="assets",
            change="Device details updated",
            details=f"IMEI {hardware.imei} metadata edited",
            actor=context.user,
            target_type="device",
            target_id=str(hardware.id),
        )

    hydrated = _load_hardware_or_404(hardware_id, context, db)
    return DeviceInventoryDetailResponse(data=_serialize_device(hydrated))


@router.post("/{hardware_id}/assign", response_model=DeviceInventoryDetailResponse)
async def assign_device(
    hardware_id: int,
    payload: DeviceAssignmentRequest,
    context: HubAccessContext = Depends(require_hub_access(*ASSIGNMENT_ROLES)),
    db: Session = Depends(get_db),
):
    """Assign hardware to a hub inventory slot or directly to a vehicle."""

    hardware = _load_hardware_or_404(hardware_id, context, db, with_relationships=True)

    vehicle_id: Optional[UUID] = payload.vehicle_id
    target_hub_id: Optional[UUID] = payload.hub_id
    asset_type = _clean_text(payload.asset_type)
    asset_name = _clean_text(payload.asset_name) or _clean_text(payload.asset_label)
    if not asset_type or not asset_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="asset_type and asset_name are required for assignment",
        )

    if vehicle_id:
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
        if not _is_global_admin(context) and vehicle.hub_id != context.hub.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vehicle does not belong to the active hub",
            )
        target_hub_id = vehicle.hub_id
    else:
        if not target_hub_id:
            target_hub_id = context.hub.id if context.hub is not None else None
        elif not _is_global_admin(context) and target_hub_id != context.hub.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot assign hardware to another hub",
            )

    if not target_hub_id and not vehicle_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="hub_id or vehicle_id is required for assignments",
        )

    _validate_technician_job_access(
        db=db,
        context=context,
        source_job_id=payload.source_job_id,
        target_hub_id=target_hub_id,
    )

    current_assignment = _active_assignment(hardware.assignments or [])
    is_reassignment = bool(
        current_assignment
        and (
            current_assignment.vehicle_id != vehicle_id
            or current_assignment.hub_id != target_hub_id
            or _clean_text(current_assignment.asset_label) != asset_name
            or _clean_text(current_assignment.asset_registration) != _clean_text(payload.asset_registration)
        )
    )

    if is_reassignment:
        reason = _clean_text(payload.reassignment_reason)
        if not reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A reassignment reason is required when moving hardware to another asset",
            )
        current_assignment.notes = _append_reason(
            current_assignment.notes,
            reason,
            prefix="Reassigned",
        )

    assign_hardware_to_vehicle(
        db,
        imei=hardware.imei,
        vehicle_id=vehicle_id,
        hub_id=target_hub_id,
        hardware_type=hardware.hardware_type,
        model=hardware.model,
        assigned_by=context.user.id,
        requested_by=context.user.id,
        technician=payload.technician,
        installed_at=payload.installed_at,
        installation_location=payload.installation_location,
        installation_latitude=payload.installation_latitude,
        installation_longitude=payload.installation_longitude,
        asset_label=asset_name,
        asset_registration=payload.asset_registration,
        notes=_combine_assignment_notes(
            free_notes=payload.notes,
            asset_type=asset_type,
            asset_name=asset_name,
            vehicle_make=payload.vehicle_make,
            vehicle_model=payload.vehicle_model,
            vehicle_year=payload.vehicle_year,
            engine_capacity=payload.engine_capacity,
            vin=payload.vin,
        ),
    )
    refreshed_for_sim = _load_hardware_or_404(hardware_id, context, db, with_relationships=True)
    if payload.sim_id is not None:
        sim = _load_sim_or_404(payload.sim_id, context, db)
        if sim.status not in {SimStatus.IN_STOCK, SimStatus.SUSPENDED, SimStatus.ASSIGNED}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected SIM is not available for assignment",
            )
        _assign_sim_to_hardware(
            db=db,
            sim=sim,
            hardware=refreshed_for_sim,
            assigned_by=context.user.id,
            hub_id=target_hub_id,
            vehicle_id=vehicle_id,
            notes=f"Linked during device assignment for asset {payload.asset_registration or asset_name}",
        )
    else:
        _sync_active_sim_assignment(
            db=db,
            hardware=refreshed_for_sim,
            hub_id=target_hub_id,
            vehicle_id=vehicle_id,
        )
    append_admin_activity(
        db,
        module="assets",
        change="Device reassigned" if is_reassignment else "Device assigned",
        details=(
            f"IMEI {hardware.imei} moved to asset {payload.asset_registration or asset_name}"
            if is_reassignment
            else f"IMEI {hardware.imei} assigned to {'vehicle' if vehicle_id else 'hub'}"
        ),
        actor=context.user,
        target_type="device",
        target_id=str(hardware.id),
    )
    refreshed = _load_hardware_or_404(hardware_id, context, db)
    return DeviceInventoryDetailResponse(data=_serialize_device(refreshed))


@router.post("/{hardware_id}/recall", response_model=DeviceInventoryDetailResponse)
async def recall_device(
    hardware_id: int,
    payload: DeviceRecallRequest,
    context: HubAccessContext = Depends(require_hub_access(*ASSIGNMENT_ROLES)),
    db: Session = Depends(get_db),
):
    """Recall installed hardware back into inventory with a reason and status."""

    hardware = _load_hardware_or_404(hardware_id, context, db, with_relationships=True)
    current_assignment = _active_assignment(hardware.assignments or [])
    if not current_assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected hardware has no active assignment to recall",
        )

    target_hub_id = current_assignment.hub_id or (current_assignment.vehicle.hub_id if current_assignment.vehicle else None)
    _validate_technician_job_access(
        db=db,
        context=context,
        source_job_id=payload.source_job_id,
        target_hub_id=target_hub_id,
    )

    reason = _clean_text(payload.reason)
    if not reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A recall reason is required",
        )
    if payload.status not in {
        HardwareStatus.IN_STOCK,
        HardwareStatus.FAULTY,
        HardwareStatus.MAINTENANCE,
        HardwareStatus.RETIRED,
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recalled hardware must return to an inventory lifecycle state",
        )

    current_assignment.notes = _append_reason(
        current_assignment.notes,
        reason,
        prefix="Recalled",
    )
    if _clean_text(payload.notes):
        current_assignment.notes = _append_reason(
            current_assignment.notes,
            payload.notes,
            prefix="Recall notes",
        )
    current_assignment.is_active = False
    current_assignment.unassigned_at = datetime.now(timezone.utc)

    active_sim_assignment = _active_sim_assignment(hardware.sim_assignments or [])
    if active_sim_assignment:
        _recall_sim_assignment(
            db=db,
            assignment=active_sim_assignment,
            status_value=SimStatus.IN_STOCK,
            reason=f"Tracker recall for IMEI {hardware.imei}",
            notes=payload.notes,
        )

    update_device_status_service(
        db,
        imei=hardware.imei,
        status=payload.status,
        notes=f"Recall reason: {reason}",
    )

    append_admin_activity(
        db,
        module="assets",
        change="Device recalled",
        details=(
            f"IMEI {hardware.imei} recalled from "
            f"{current_assignment.asset_registration or current_assignment.asset_label or 'unlabelled asset'} "
            f"as {payload.status.value}"
        ),
        actor=context.user,
        target_type="device",
        target_id=str(hardware.id),
    )

    refreshed = _load_hardware_or_404(hardware_id, context, db)
    return DeviceInventoryDetailResponse(data=_serialize_device(refreshed))


@router.post("/{hardware_id}/reassign", response_model=DeviceInventoryDetailResponse)
async def reassign_device(
    hardware_id: int,
    payload: DeviceReassignmentRequest,
    context: HubAccessContext = Depends(require_hub_access(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    """Recall currently installed hardware, mark it faulty, and replace it with another unit."""

    faulty_hardware = _load_hardware_or_404(hardware_id, context, db, with_relationships=True)
    replacement_hardware = _load_hardware_or_404(payload.replacement_hardware_id, context, db, with_relationships=True)

    if replacement_hardware.id == faulty_hardware.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Replacement hardware must be different from faulty hardware")

    current_assignment = _active_assignment(faulty_hardware.assignments or [])
    if not current_assignment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected faulty hardware has no active assignment")

    current_assignment.notes = _append_reason(
        current_assignment.notes,
        payload.faulty_reason or "Recall flagged during replacement workflow",
        prefix="Recalled",
    )
    current_assignment.is_active = False
    current_assignment.unassigned_at = datetime.now(timezone.utc)

    recall_reason = payload.faulty_reason or "Recall flagged during replacement workflow"
    update_device_status_service(
        db,
        imei=faulty_hardware.imei,
        status=HardwareStatus.FAULTY,
        notes=recall_reason,
    )

    replacement_asset_type = _clean_text(payload.asset_type)
    replacement_asset_name = _clean_text(payload.asset_name) or _clean_text(payload.asset_label)
    replacement_notes = (
        _combine_assignment_notes(
            free_notes=payload.notes,
            asset_type=replacement_asset_type,
            asset_name=replacement_asset_name or current_assignment.asset_label,
            vehicle_make=payload.vehicle_make,
            vehicle_model=payload.vehicle_model,
            vehicle_year=payload.vehicle_year,
            engine_capacity=payload.engine_capacity,
            vin=payload.vin,
        )
        if any(
            [
                payload.notes,
                replacement_asset_type,
                replacement_asset_name,
                payload.vehicle_make,
                payload.vehicle_model,
                payload.vehicle_year,
                payload.engine_capacity,
                payload.vin,
            ]
        )
        else current_assignment.notes
    )
    assign_hardware_to_vehicle(
        db,
        imei=replacement_hardware.imei,
        vehicle_id=current_assignment.vehicle_id,
        hub_id=current_assignment.hub_id,
        hardware_type=replacement_hardware.hardware_type,
        model=replacement_hardware.model,
        assigned_by=context.user.id,
        requested_by=context.user.id,
        technician=payload.technician,
        installed_at=payload.installed_at or current_assignment.installed_at,
        installation_location=payload.installation_location or current_assignment.installation_location,
        installation_latitude=payload.installation_latitude
        if payload.installation_latitude is not None
        else (
            float(current_assignment.installation_latitude)
            if current_assignment.installation_latitude is not None
            else None
        ),
        installation_longitude=payload.installation_longitude
        if payload.installation_longitude is not None
        else (
            float(current_assignment.installation_longitude)
            if current_assignment.installation_longitude is not None
            else None
        ),
        asset_label=replacement_asset_name or current_assignment.asset_label,
        asset_registration=payload.asset_registration or current_assignment.asset_registration,
        notes=replacement_notes,
    )
    refreshed_replacement = _load_hardware_or_404(payload.replacement_hardware_id, context, db, with_relationships=True)
    active_faulty_sim_assignment = _active_sim_assignment(faulty_hardware.sim_assignments or [])
    if active_faulty_sim_assignment and active_faulty_sim_assignment.sim:
        _assign_sim_to_hardware(
            db=db,
            sim=active_faulty_sim_assignment.sim,
            hardware=refreshed_replacement,
            assigned_by=context.user.id,
            hub_id=current_assignment.hub_id,
            vehicle_id=current_assignment.vehicle_id,
            notes=f"Moved from faulty IMEI {faulty_hardware.imei} during replacement",
        )

    append_admin_activity(
        db,
        module="assets",
        change="Device replaced",
        details=(
            f"Faulty IMEI {faulty_hardware.imei} replaced with IMEI {replacement_hardware.imei} "
            f"for asset {payload.asset_registration or current_assignment.asset_registration or 'unlabelled'}"
        ),
        actor=context.user,
        target_type="device",
        target_id=str(replacement_hardware.id),
    )

    refreshed = _load_hardware_or_404(replacement_hardware.id, context, db)
    return DeviceInventoryDetailResponse(data=_serialize_device(refreshed))


@router.delete("/{hardware_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    hardware_id: int,
    context: HubAccessContext = Depends(require_hub_access(*WRITE_ROLES)),
    db: Session = Depends(get_db),
):
    """Remove a hardware record from inventory."""

    hardware = _load_hardware_or_404(hardware_id, context, db, with_relationships=False)
    imei = hardware.imei

    open_jobs_count = (
        db.query(func.count(TechnicianJob.id))
        .filter(
            TechnicianJob.hardware_id == hardware.id,
            TechnicianJob.status.in_(
                [
                    TechnicianJobStatus.pending,
                    TechnicianJobStatus.assigned,
                    TechnicianJobStatus.in_progress,
                ]
            ),
        )
        .scalar()
        or 0
    )
    if open_jobs_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete hardware with open technician jobs. Complete or cancel the jobs first.",
        )

    archived_jobs = (
        db.query(TechnicianJob)
        .filter(TechnicianJob.hardware_id == hardware.id)
        .all()
    )
    archived_job_count = len(archived_jobs)
    for job in archived_jobs:
        db.delete(job)

    db.delete(hardware)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete hardware while linked records still exist.",
        )
    append_admin_activity(
        db,
        module="assets",
        change="Device deleted",
        details=(
            f"IMEI {imei} removed from inventory"
            + (f" (cleared {archived_job_count} technician job records)" if archived_job_count else "")
        ),
        actor=context.user,
        target_type="device",
        target_id=str(hardware_id),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
