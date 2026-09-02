"""Hardware inventory service helpers."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterable, Optional, Union
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.hub import Hub
from app.models.hardware import HardwareAssignment, HardwareInventory, HardwareStatus
from app.models.pairing import DevicePairing, PairingStatus
from app.models.user import User
from app.models.vehicle import Vehicle

logger = logging.getLogger(__name__)


def _clean(value: Optional[str]) -> Optional[str]:
    """Return a trimmed string or ``None`` when empty."""

    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _merge_notes(existing: Optional[str], addition: Optional[str]) -> Optional[str]:
    """Append notes while keeping the stored text compact."""

    addition = _clean(addition)
    if not addition:
        return existing
    if not existing:
        return addition
    return f"{existing.rstrip()}\n{addition}"


def _get_hardware_by_imei(db: Session, imei: str) -> Optional[HardwareInventory]:
    return (
        db.query(HardwareInventory)
        .filter(HardwareInventory.imei == imei)
        .one_or_none()
    )


def _resolve_user_id(db: Session, reference: Optional[Union[str, UUID]]) -> Optional[UUID]:
    """Map a UUID/email identifier into an internal user ID."""

    if reference is None:
        return None
    if isinstance(reference, UUID):
        user = db.query(User).filter(User.id == reference).one_or_none()
        return user.id if user else None

    normalized = _clean(str(reference))
    if not normalized:
        return None

    try:
        as_uuid = UUID(normalized)
    except ValueError:
        as_uuid = None
    if as_uuid:
        user = db.query(User).filter(User.id == as_uuid).one_or_none()
        if user:
            return user.id

    if "@" in normalized:
        user = (
            db.query(User)
            .filter(func.lower(User.email) == normalized.lower())
            .one_or_none()
        )
        if user:
            return user.id

    return None


def upsert_hardware(
    db: Session,
    *,
    imei: str,
    hardware_type: Optional[str] = None,
    model: Optional[str] = None,
    manufacturer: Optional[str] = None,
    firmware_version: Optional[str] = None,
    serial_number: Optional[str] = None,
    notes: Optional[str] = None,
) -> HardwareInventory:
    """Ensure an inventory record exists for the provided IMEI."""

    if not _clean(imei):
        raise ValueError("IMEI is required to upsert hardware")

    hardware = _get_hardware_by_imei(db, imei)
    if hardware is None:
        hardware = HardwareInventory(
            imei=imei.strip(),
            hardware_type=_clean(hardware_type),
            model=_clean(model),
            manufacturer=_clean(manufacturer),
            firmware_version=_clean(firmware_version),
            serial_number=_clean(serial_number),
            notes=_clean(notes),
        )
        db.add(hardware)
        db.flush()
        logger.debug("Created inventory record for IMEI %s", imei)
        return hardware

    if hardware_type:
        hardware.hardware_type = _clean(hardware_type)
    if model:
        hardware.model = _clean(model)
    if manufacturer:
        hardware.manufacturer = _clean(manufacturer)
    if firmware_version:
        hardware.firmware_version = _clean(firmware_version)
    if serial_number and not hardware.serial_number:
        hardware.serial_number = _clean(serial_number)
    if notes:
        hardware.notes = _merge_notes(hardware.notes, notes)
    return hardware


def _close_active_assignments(db: Session, hardware: HardwareInventory) -> None:
    """Mark any active assignments as inactive before creating a new one."""

    active_assignments = (
        db.query(HardwareAssignment)
        .filter(
            HardwareAssignment.hardware_id == hardware.id,
            HardwareAssignment.is_active.is_(True),
        )
        .all()
    )
    for assignment in active_assignments:
        assignment.is_active = False
        assignment.unassigned_at = datetime.utcnow()


def _hub_id_for_vehicle(db: Session, vehicle_id: Optional[UUID]) -> Optional[UUID]:
    if not vehicle_id:
        return None
    return db.query(Vehicle.hub_id).filter(Vehicle.id == vehicle_id).scalar()


def _refresh_hub_counters(db: Session, hub_ids: set[UUID]) -> None:
    if not hub_ids:
        return

    for hub_id in hub_ids:
        if not hub_id:
            continue
        vehicle_count = db.query(func.count(Vehicle.id)).filter(Vehicle.hub_id == hub_id).scalar() or 0
        device_count = (
            db.query(func.count(func.distinct(HardwareAssignment.hardware_id)))
            .outerjoin(Vehicle, Vehicle.id == HardwareAssignment.vehicle_id)
            .filter(
                HardwareAssignment.is_active.is_(True),
                (HardwareAssignment.hub_id == hub_id) | (Vehicle.hub_id == hub_id),
            )
            .scalar()
            or 0
        )
        db.query(Hub).filter(Hub.id == hub_id).update(
            {
                Hub.vehicle_count: int(vehicle_count),
                Hub.device_count: int(device_count),
            },
            synchronize_session=False,
        )


def _close_asset_assignments(
    db: Session,
    *,
    hub_id: Optional[UUID],
    vehicle_id: Optional[UUID],
    asset_registration: Optional[str],
) -> None:
    """Ensure only one active hardware assignment exists per asset target."""

    query = db.query(HardwareAssignment).filter(HardwareAssignment.is_active.is_(True))

    if vehicle_id:
        assignments = query.filter(HardwareAssignment.vehicle_id == vehicle_id).all()
    elif hub_id and asset_registration:
        assignments = query.filter(
            HardwareAssignment.hub_id == hub_id,
            HardwareAssignment.asset_registration == asset_registration,
        ).all()
    else:
        assignments = []

    for assignment in assignments:
        assignment.is_active = False
        assignment.unassigned_at = datetime.utcnow()


def _coerce_pairing_status(status: Union[str, PairingStatus]) -> PairingStatus:
    if isinstance(status, PairingStatus):
        return status
    try:
        return PairingStatus(str(status))
    except ValueError as exc:  # pragma: no cover - guard
        raise ValueError(f"Unsupported pairing status: {status}") from exc


def _upsert_device_pairing(
    db: Session,
    *,
    hardware_id: int,
    vehicle_id: UUID,
    requested_by: Optional[UUID],
    approved_by: Optional[UUID],
    status: PairingStatus,
    notes: Optional[str],
) -> DevicePairing:
    pairing = (
        db.query(DevicePairing)
        .filter(
            DevicePairing.hardware_id == hardware_id,
            DevicePairing.vehicle_id == vehicle_id,
        )
        .order_by(DevicePairing.created_at.desc())
        .first()
    )

    normalized_notes = _clean(notes)
    approved_at = datetime.utcnow() if status == PairingStatus.approved else None

    if pairing:
        pairing.status = status
        if requested_by:
            pairing.requested_by = requested_by
        if approved_by:
            pairing.approved_by = approved_by
        if approved_at:
            pairing.approved_at = approved_at
        if normalized_notes:
            pairing.notes = _merge_notes(pairing.notes, normalized_notes)
        return pairing

    pairing = DevicePairing(
        hardware_id=hardware_id,
        vehicle_id=vehicle_id,
        requested_by=requested_by,
        approved_by=approved_by,
        status=status,
        notes=normalized_notes,
        approved_at=approved_at,
    )
    db.add(pairing)
    return pairing


def _format_submission_context(
    *,
    technician: Optional[str],
    installation_date: Optional[datetime],
    photos: Optional[Iterable[str]],
    notes: Optional[str],
) -> Optional[str]:
    pieces = []
    if technician:
        pieces.append(f"Technician: {technician.strip()}")
    if installation_date:
        pieces.append(f"Installed: {installation_date.isoformat()}")
    if photos:
        filtered = [p.strip() for p in photos if p]
        if filtered:
            pieces.append("Photos: " + ", ".join(filtered))
    if notes:
        pieces.append(notes.strip())
    if not pieces:
        return None
    return " | ".join(pieces)


def record_pairing_submission(
    db: Session,
    *,
    imei: str,
    vehicle_id: UUID,
    hub_id: Optional[UUID],
    hardware_type: Optional[str],
    model: Optional[str],
    technician: Optional[str],
    requested_by: Optional[Union[str, UUID]],
    status: Union[str, PairingStatus],
    notes: Optional[str],
    installation_date: Optional[datetime],
    photos: Optional[Iterable[str]],
) -> str:
    """Persist a pending pairing workflow entry before approval."""

    pairing_status = _coerce_pairing_status(status)
    hardware = upsert_hardware(
        db,
        imei=imei,
        hardware_type=hardware_type,
        model=model,
        notes=notes,
    )
    submission_details = _format_submission_context(
        technician=technician,
        installation_date=installation_date,
        photos=photos,
        notes=notes,
    )

    pairing = DevicePairing(
        hardware_id=hardware.id,
        vehicle_id=vehicle_id,
        requested_by=_resolve_user_id(db, requested_by),
        status=pairing_status,
        notes=submission_details,
    )
    db.add(pairing)

    try:
        db.commit()
    except IntegrityError as exc:  # pragma: no cover - defensive
        db.rollback()
        logger.exception("Failed to persist pairing submission for IMEI %s", imei)
        raise ValueError("Failed to record pairing submission") from exc

    db.refresh(pairing)
    logger.info(
        "Recorded pairing submission imei=%s vehicle=%s pairing_id=%s status=%s",
        imei,
        vehicle_id,
        pairing.id,
        pairing.status,
    )
    return str(pairing.id)


def reject_pairing(
    db: Session,
    *,
    imei: str,
    vehicle_id: UUID,
    hub_id: Optional[UUID],
    verifier: Optional[Union[str, UUID]],
    notes: Optional[str],
) -> str:
    """Mark the latest pairing for the hardware as rejected."""

    hardware = _get_hardware_by_imei(db, imei)
    if hardware is None:
        raise ValueError("Cannot reject pairing for unknown hardware")

    pairing = (
        db.query(DevicePairing)
        .filter(
            DevicePairing.hardware_id == hardware.id,
            DevicePairing.vehicle_id == vehicle_id,
        )
        .order_by(DevicePairing.created_at.desc())
        .first()
    )
    if pairing is None:
        raise ValueError("No pairing submission found to reject")

    pairing.status = PairingStatus.rejected
    pairing.approved_by = _resolve_user_id(db, verifier)
    pairing.notes = _merge_notes(pairing.notes, notes)
    pairing.approved_at = datetime.utcnow()

    try:
        db.commit()
    except IntegrityError as exc:  # pragma: no cover - defensive
        db.rollback()
        logger.exception("Failed to reject pairing for IMEI %s", imei)
        raise ValueError("Failed to update pairing status") from exc

    db.refresh(pairing)
    logger.info(
        "Rejected pairing imei=%s vehicle=%s pairing_id=%s",
        imei,
        vehicle_id,
        pairing.id,
    )
    return str(pairing.id)


def assign_hardware_to_vehicle(
    db: Session,
    *,
    imei: str,
    vehicle_id: Optional[UUID],
    hub_id: Optional[UUID],
    hardware_type: Optional[str],
    model: Optional[str],
    assigned_by: Optional[Union[str, UUID]] = None,
    requested_by: Optional[Union[str, UUID]] = None,
    technician: Optional[str] = None,
    installed_at: Optional[datetime] = None,
    installation_location: Optional[str] = None,
    installation_latitude: Optional[float] = None,
    installation_longitude: Optional[float] = None,
    asset_label: Optional[str] = None,
    asset_registration: Optional[str] = None,
    status: Union[str, PairingStatus] = PairingStatus.approved,
    notes: Optional[str] = None,
    installation_date: Optional[datetime] = None,
    photos: Optional[Iterable[str]] = None,
    verification_note: Optional[str] = None,
) -> str:
    """Assign a hardware device to a vehicle/hub and sync DevicePairing metadata."""

    if not (vehicle_id or hub_id):
        raise ValueError("Either vehicle_id or hub_id must be provided for an assignment")

    pairing_status = _coerce_pairing_status(status)
    hardware = upsert_hardware(
        db,
        imei=imei,
        hardware_type=hardware_type,
        model=model,
        notes=_merge_notes(notes, verification_note),
    )

    impacted_hub_ids: set[UUID] = set()
    existing_active = (
        db.query(HardwareAssignment)
        .filter(
            HardwareAssignment.hardware_id == hardware.id,
            HardwareAssignment.is_active.is_(True),
        )
        .all()
    )
    for existing in existing_active:
        if existing.hub_id:
            impacted_hub_ids.add(existing.hub_id)
        elif existing.vehicle_id:
            old_hub_id = _hub_id_for_vehicle(db, existing.vehicle_id)
            if old_hub_id:
                impacted_hub_ids.add(old_hub_id)

    _close_active_assignments(db, hardware)
    _close_asset_assignments(
        db,
        hub_id=hub_id,
        vehicle_id=vehicle_id,
        asset_registration=_clean(asset_registration),
    )

    assignment = HardwareAssignment(
        hardware_id=hardware.id,
        vehicle_id=vehicle_id,
        hub_id=hub_id,
        assigned_by=_resolve_user_id(db, assigned_by),
        installed_at=installed_at,
        installation_location=_clean(installation_location),
        installation_latitude=installation_latitude,
        installation_longitude=installation_longitude,
        asset_label=_clean(asset_label),
        asset_registration=_clean(asset_registration),
        notes=_clean(notes),
    )
    db.add(assignment)
    if hub_id:
        impacted_hub_ids.add(hub_id)
    elif vehicle_id:
        resolved_hub_id = _hub_id_for_vehicle(db, vehicle_id)
        if resolved_hub_id:
            impacted_hub_ids.add(resolved_hub_id)

    hardware.status = HardwareStatus.ASSIGNED if (vehicle_id or hub_id) else HardwareStatus.IN_STOCK

    pairing: Optional[DevicePairing] = None
    if vehicle_id:
        pairing = _upsert_device_pairing(
            db,
            hardware_id=hardware.id,
            vehicle_id=vehicle_id,
            requested_by=_resolve_user_id(db, requested_by),
            approved_by=assignment.assigned_by,
            status=pairing_status,
            notes=_merge_notes(_format_submission_context(
                technician=technician,
                installation_date=installation_date,
                photos=photos,
                notes=notes,
            ), verification_note),
        )

    _refresh_hub_counters(db, impacted_hub_ids)

    try:
        db.commit()
    except IntegrityError as exc:  # pragma: no cover - database guard
        db.rollback()
        logger.exception("Failed to persist hardware assignment for IMEI %s", imei)
        raise ValueError("Failed to persist hardware assignment") from exc

    db.refresh(assignment)
    if pairing is not None:
        db.refresh(pairing)
    logger.info(
        "Assigned hardware imei=%s vehicle=%s hub=%s assignment_id=%s pairing_id=%s",
        imei,
        vehicle_id,
        hub_id,
        assignment.id,
        pairing.id if pairing else None,
    )
    reference = pairing.id if pairing else assignment.id
    return str(reference)


def _coerce_status(status: Union[str, HardwareStatus]) -> HardwareStatus:
    if isinstance(status, HardwareStatus):
        return status
    try:
        return HardwareStatus(str(status))
    except ValueError as exc:
        raise ValueError(f"Unsupported hardware status: {status}") from exc


def update_device_status(
    db: Session,
    imei: str,
    status: Union[str, HardwareStatus],
    notes: Optional[str] = None,
) -> None:
    """Update the lifecycle status of a hardware device."""

    hardware = _get_hardware_by_imei(db, imei)
    if hardware is None:
        hardware = HardwareInventory(imei=imei, status=HardwareStatus.IN_STOCK)
        db.add(hardware)
        db.flush()
        logger.debug("Created placeholder inventory record for status update IMEI %s", imei)

    hardware.status = _coerce_status(status)

    if notes:
        hardware.notes = _merge_notes(hardware.notes, notes)

    impacted_hub_ids: set[UUID] = set()
    active_assignments = (
        db.query(HardwareAssignment)
        .filter(
            HardwareAssignment.hardware_id == hardware.id,
            HardwareAssignment.is_active.is_(True),
        )
        .all()
    )
    for assignment in active_assignments:
        if assignment.hub_id:
            impacted_hub_ids.add(assignment.hub_id)
        elif assignment.vehicle_id:
            resolved_hub_id = _hub_id_for_vehicle(db, assignment.vehicle_id)
            if resolved_hub_id:
                impacted_hub_ids.add(resolved_hub_id)

    if hardware.status != HardwareStatus.ASSIGNED:
        _close_active_assignments(db, hardware)

    _refresh_hub_counters(db, impacted_hub_ids)
    db.commit()
    logger.info("Updated hardware status imei=%s status=%s", imei, hardware.status)
