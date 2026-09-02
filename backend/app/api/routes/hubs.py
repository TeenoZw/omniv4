"""Hub management routes aligned with admin portal provisioning flows."""
from __future__ import annotations

import re
from typing import Any, Optional
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import String, func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.auth import HubAccessContext, require_hub_access, require_role
from app.core.config import settings
from app.core.database import get_db
from app.models.device import Device
from app.models.hardware import HardwareAssignment, HardwareInventory, HardwareStatus, SimInventory, SimStatus
from app.core.security import get_password_hash
from app.models import Hub, HubMembership, HubMembershipStatus, User
from app.models.subscription import Subscription
from app.models.technician import Technician
from app.models.technician_job import TechnicianJob, TechnicianJobStatus
from app.models.user import UserRole
from app.models.vehicle import Vehicle
from app.schemas.hubs import (
    HubAssetCreate,
    HubAssetUpdate,
    HubAssetDetailResponse,
    HubAssetAssignmentHistoryItem,
    HubAssetListData,
    HubAssetListResponse,
    HubAssetPaginationMeta,
    HubAssetResponse,
    HubAssetDeviceResponse,
    HubBulkDeleteRequest,
    HubCreate,
    HubResponse,
    HubUpdate,
    HubUserCreate,
    HubUserUpdate,
    VinDecodeRequest,
    VinDecodeResponse,
)
from app.services.hubs import _resolve_unique_code
from app.services.admin_activity import append_admin_activity
from app.services.hardware import assign_hardware_to_vehicle
from app.api.routes.devices import _assign_sim_to_hardware
from app.services.vin_decoder import decode_vin

router = APIRouter()

READ_ROLES = (
    UserRole.admin,
    UserRole.technician,
)
RECYCLE_RETENTION_DAYS = 30


def _normalize_email(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _clean_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _is_bootstrap_admin_email(email: Optional[str]) -> bool:
    return _normalize_email(email) == _normalize_email(settings.bootstrap_admin_email)


def _is_admin_role(role: Any) -> bool:
    return str(getattr(role, "value", role)).strip().lower() == UserRole.admin.value


def _is_internal_role(role: Any) -> bool:
    normalized = str(getattr(role, "value", role)).strip().lower()
    return normalized in {UserRole.admin.value, UserRole.technician.value}


def _enforce_admin_role_protection(user: User, requested_role: UserRole) -> None:
    if requested_role == UserRole.admin:
        return
    if _is_admin_role(user.role) or _is_bootstrap_admin_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin accounts cannot be downgraded via hub access control",
        )


def _normalize_hub_type(value: Optional[str]) -> str:
    normalized = (value or "business").strip().lower()
    if normalized in {"individual", "personal"}:
        return "individual"
    if normalized in {"business", "company", "corporate"}:
        return "business"
    return "business"


def _tier_from_hub_type(hub_type: Optional[str]) -> str:
    return "individual" if _normalize_hub_type(hub_type) == "individual" else "business"


def _normalize_subscription_tier(value: Optional[str], hub_type: Optional[str] = None) -> str:
    normalized = (value or "").strip().lower()
    if normalized in {"individual", "personal", "basic", "free"}:
        return "individual"
    if normalized in {"business", "company", "corporate", "pro", "enterprise"}:
        return "business"
    return _tier_from_hub_type(hub_type)


def _subscription_storage_tier(value: Optional[str], hub_type: Optional[str] = None) -> str:
    """Map app-level tier labels to the legacy DB enum values used by subscriptions.tier."""
    normalized = _normalize_subscription_tier(value, hub_type)
    return "free" if normalized == "individual" else "pro"


def _normalize_subscription_status(value: Optional[str]) -> str:
    normalized = (value or "provisioning").strip().lower()
    if normalized in {"deactivated", "deactivate"}:
        return "inactive"
    if normalized in {"active", "suspended", "provisioning", "inactive"}:
        return normalized
    return "provisioning"


def _serialize_hub(
    hub: Hub,
    *,
    device_count: int | None = None,
    vehicle_count: int | None = None,
    subscription_days_left: int | None = None,
    subscription_start_date: str | None = None,
    subscription_end_date: str | None = None,
    devices: Optional[list[dict[str, Any]]] = None,
) -> HubResponse:
    return HubResponse(
        id=str(hub.id),
        code=hub.code,
        name=hub.name,
        type=hub.hub_type or "company",
        tier=_normalize_subscription_tier(hub.subscription_tier, hub.hub_type),
        payment_method=hub.payment_method or "manual_invoice",
        billing_cycle=hub.billing_cycle or "monthly",
        status=hub.status or "active",
        timezone=hub.timezone,
        country=hub.country,
        city=hub.city,
        address=hub.address_line,
        go_live_date=hub.go_live_date.isoformat() if hub.go_live_date else None,
        notes=hub.notes,
        device_count=device_count if device_count is not None else (hub.device_count or 0),
        vehicle_count=vehicle_count if vehicle_count is not None else (hub.vehicle_count or 0),
        primary_contact={
          "name": hub.primary_contact_name,
          "email": hub.primary_contact_email,
          "phone": hub.primary_contact_phone,
        },
        billing_contact={
          "name": hub.billing_contact_name,
                    "email": hub.billing_contact_email,
                    "phone": hub.billing_contact_phone,
        },
        currency=hub.currency,
        subscription_days_left=subscription_days_left,
        subscription_start_date=subscription_start_date,
        subscription_end_date=subscription_end_date,
        users=[
            {
                "id": str(m.user.id),
                "name": m.user.name,
                "email": m.user.email,
                "role": m.role.value if hasattr(m.role, "value") else str(m.role),
            }
            for m in (hub.memberships or [])
            if m.user is not None and not _is_internal_role(m.user.role)
        ],
        devices=devices or [],
        created_at=hub.created_at,
        updated_at=hub.updated_at,
    )


def _active_hub_devices(db: Session, hub_id: UUID) -> list[dict[str, Any]]:
    rows = (
        db.query(HardwareAssignment, HardwareInventory, Vehicle)
        .join(HardwareInventory, HardwareInventory.id == HardwareAssignment.hardware_id)
        .outerjoin(Vehicle, Vehicle.id == HardwareAssignment.vehicle_id)
        .filter(
            HardwareAssignment.is_active.is_(True),
            or_(
                HardwareAssignment.hub_id == hub_id,
                Vehicle.hub_id == hub_id,
            ),
        )
        .order_by(HardwareAssignment.assigned_at.desc())
        .all()
    )
    payload: list[dict[str, Any]] = []
    for assignment, hardware, vehicle in rows:
        payload.append(
            {
                "assignment_id": assignment.id,
                "hardware_id": hardware.id,
                "imei": hardware.imei,
                "model": hardware.model,
                "hardware_type": hardware.hardware_type,
                "status": hardware.status.value if hasattr(hardware.status, "value") else str(hardware.status),
                "asset_label": assignment.asset_label,
                "asset_registration": assignment.asset_registration,
                "installation_location": assignment.installation_location,
                "technician": assignment.assigned_user.name if assignment.assigned_user else None,
                "assigned_at": assignment.assigned_at,
                "installed_at": assignment.installed_at,
                "vehicle_id": str(vehicle.id) if vehicle else None,
                "vehicle_label": (
                    vehicle.license_plate
                    if vehicle and vehicle.license_plate
                    else (vehicle.vin if vehicle and vehicle.vin else vehicle.model if vehicle else None)
                ),
            }
        )
    return payload


@router.post("/vin/decode", response_model=VinDecodeResponse)
async def decode_asset_vin(
    payload: VinDecodeRequest,
    actor: User = Depends(require_role(UserRole.admin, UserRole.technician)),
):
    """Decode VIN metadata for onboarding and asset maintenance workflows."""
    result = await decode_vin(payload.vin)
    return VinDecodeResponse(**result)


def _serialize_assignment_device(
    assignment: HardwareAssignment,
    hardware: HardwareInventory,
    vehicle: Vehicle | None,
) -> HubAssetDeviceResponse:
    assignment_history: list[HubAssetAssignmentHistoryItem] = []
    history_rows = sorted(
        hardware.assignments or [],
        key=lambda item: item.assigned_at or item.created_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    for history in history_rows:
        history_vehicle = history.vehicle
        history_hub = history.hub or (history_vehicle.hub if history_vehicle else None)
        target = "vehicle" if history.vehicle_id else ("hub" if history.hub_id else "inventory")
        assignment_history.append(
            HubAssetAssignmentHistoryItem(
                id=history.id,
                target=target,
                hub_id=str(history_hub.id) if history_hub else (str(history.hub_id) if history.hub_id else None),
                hub_name=history_hub.name if history_hub else (history.hub.name if history.hub else None),
                vehicle_id=str(history.vehicle_id) if history.vehicle_id else None,
                vehicle_label=(
                    history_vehicle.license_plate
                    if history_vehicle and history_vehicle.license_plate
                    else (
                        history_vehicle.vin
                        if history_vehicle and history_vehicle.vin
                        else history_vehicle.model if history_vehicle else None
                    )
                ),
                technician=history.assigned_user.name if history.assigned_user else None,
                assigned_at=history.assigned_at,
                installed_at=history.installed_at,
                unassigned_at=history.unassigned_at,
                installation_location=history.installation_location,
                installation_latitude=float(history.installation_latitude) if history.installation_latitude is not None else None,
                installation_longitude=float(history.installation_longitude) if history.installation_longitude is not None else None,
                asset_label=history.asset_label,
                asset_registration=history.asset_registration,
                notes=history.notes,
                is_active=bool(history.is_active),
            )
        )
    return HubAssetDeviceResponse(
        assignment_id=assignment.id,
        hardware_id=hardware.id,
        imei=hardware.imei,
        serial_number=hardware.serial_number,
        model=hardware.model,
        hardware_type=hardware.hardware_type,
        manufacturer=hardware.manufacturer,
        firmware_version=hardware.firmware_version,
        status=hardware.status.value if hasattr(hardware.status, "value") else str(hardware.status),
        asset_label=assignment.asset_label,
        asset_registration=assignment.asset_registration,
        installation_location=assignment.installation_location,
        technician=assignment.assigned_user.name if assignment.assigned_user else None,
        assigned_at=assignment.assigned_at,
        installed_at=assignment.installed_at,
        vehicle_id=str(vehicle.id) if vehicle else None,
        vehicle_label=(
            vehicle.license_plate
            if vehicle and vehicle.license_plate
            else (vehicle.vin if vehicle and vehicle.vin else vehicle.model if vehicle else None)
        ),
        assignment_history=assignment_history,
    )


def _serialize_vehicle_asset(
    hub: Hub,
    vehicle: Vehicle,
    devices: list[HubAssetDeviceResponse] | None = None,
) -> HubAssetResponse | HubAssetDetailResponse:
    assigned_devices = devices or []
    last_assignment_at = None
    if assigned_devices:
        last_assignment_at = max(
            (
                device.installed_at or device.assigned_at
                for device in assigned_devices
                if device.installed_at or device.assigned_at
            ),
            default=None,
        )
    payload = dict(
        id=str(vehicle.id),
        asset_type=vehicle.asset_type,
        asset_name=vehicle.asset_name,
        asset_type_other=vehicle.asset_type_other,
        registration=vehicle.license_plate,
        label=vehicle.asset_name or vehicle.model or vehicle.make or vehicle.vin or vehicle.license_plate,
        vin=vehicle.vin,
        make=vehicle.make,
        model=vehicle.model,
        year=vehicle.year,
        color=vehicle.color,
        engine_capacity=vehicle.engine_capacity,
        co2_emissions=vehicle.co2_emissions,
        fuel_type=vehicle.fuel_type,
        status=vehicle.status.value if hasattr(vehicle.status, "value") else str(vehicle.status),
        notes=vehicle.notes,
        tracking_state="tracked" if assigned_devices else "unassigned",
        source_job_id=str(vehicle.source_job_id) if vehicle.source_job_id else None,
        assigned_device_count=len(assigned_devices),
        last_assignment_at=last_assignment_at,
    )
    if devices is None:
        return HubAssetResponse(**payload)
    return HubAssetDetailResponse(
        **payload,
        hub_id=str(hub.id),
        hub_code=hub.code,
        hub_name=hub.name,
        devices=assigned_devices,
    )


def _asset_slug(value: Optional[str]) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower())
    return cleaned.strip("-") or "unlabelled"



def _virtual_asset_id(hub_id: UUID, registration: Optional[str], label: Optional[str]) -> str:
    return f"virtual:{hub_id}:{_asset_slug(registration)}:{_asset_slug(label)}"



def _detail_to_summary(detail: HubAssetDetailResponse) -> HubAssetResponse:
    return HubAssetResponse(
        id=detail.id,
        asset_type=detail.asset_type,
        asset_name=detail.asset_name,
        asset_type_other=detail.asset_type_other,
        registration=detail.registration,
        label=detail.label,
        vin=detail.vin,
        make=detail.make,
        model=detail.model,
        year=detail.year,
        color=detail.color,
        engine_capacity=detail.engine_capacity,
        co2_emissions=detail.co2_emissions,
        fuel_type=detail.fuel_type,
        status=detail.status,
        notes=detail.notes,
        tracking_state=detail.tracking_state,
        source_job_id=detail.source_job_id,
        assigned_device_count=detail.assigned_device_count,
        last_assignment_at=detail.last_assignment_at,
    )



def _build_virtual_asset_details(
    db: Session,
    hub: Hub,
    *,
    search: Optional[str],
    status_filter: Optional[str],
) -> list[HubAssetDetailResponse]:
    assignment_rows = (
        db.query(HardwareAssignment, HardwareInventory)
        .join(HardwareInventory, HardwareInventory.id == HardwareAssignment.hardware_id)
        .options(
            joinedload(HardwareAssignment.assigned_user),
            joinedload(HardwareInventory.assignments).joinedload(HardwareAssignment.vehicle).joinedload(Vehicle.hub),
            joinedload(HardwareInventory.assignments).joinedload(HardwareAssignment.hub),
            joinedload(HardwareInventory.assignments).joinedload(HardwareAssignment.assigned_user),
        )
        .filter(
            HardwareAssignment.is_active.is_(True),
            HardwareAssignment.hub_id == hub.id,
            HardwareAssignment.vehicle_id.is_(None),
        )
        .order_by(HardwareAssignment.assigned_at.desc())
        .all()
    )

    grouped: dict[tuple[str, str], list[tuple[HardwareAssignment, HardwareInventory]]] = {}
    for assignment, hardware in assignment_rows:
        key = (
            (assignment.asset_registration or "").strip().lower(),
            (assignment.asset_label or "").strip().lower(),
        )
        grouped.setdefault(key, []).append((assignment, hardware))

    virtual_assets: list[HubAssetDetailResponse] = []
    search_term = (search or "").strip().lower()
    normalized_status = (status_filter or "").strip().lower()

    for (registration_key, label_key), rows in grouped.items():
        latest_assignment, _ = rows[0]
        registration = latest_assignment.asset_registration or None
        label = latest_assignment.asset_label or None
        detail = HubAssetDetailResponse(
            id=_virtual_asset_id(hub.id, registration, label),
            registration=registration,
            label=label or registration or "Unlabelled asset",
            vin=None,
            make=None,
            model=None,
            year=None,
            fuel_type=None,
            status="assigned",
            notes=latest_assignment.notes,
            assigned_device_count=len(rows),
            last_assignment_at=latest_assignment.installed_at or latest_assignment.assigned_at,
            hub_id=str(hub.id),
            hub_code=hub.code,
            hub_name=hub.name,
            devices=[
                _serialize_assignment_device(assignment, hardware, None)
                for assignment, hardware in rows
            ],
        )
        if search_term:
            haystack = " ".join(
                filter(
                    None,
                    [
                        registration,
                        label,
                        *(hardware.imei for _, hardware in rows if hardware.imei),
                        *(hardware.model for _, hardware in rows if hardware.model),
                    ],
                )
            ).lower()
            if search_term not in haystack:
                continue
        if normalized_status and normalized_status != (detail.status or "").lower():
            continue
        virtual_assets.append(detail)

    return virtual_assets



def _hub_asset_index(
    db: Session,
    hub: Hub,
) -> tuple[list[HubAssetResponse], dict[str, HubAssetDetailResponse], int]:
    return _hub_asset_index_paginated(
        db,
        hub,
        page=1,
        limit=100000,
        search=None,
        status_filter=None,
        sim_filter=None,
        source_job_id=None,
    )



def _hub_asset_index_paginated(
    db: Session,
    hub: Hub,
    *,
    page: int,
    limit: int,
    search: Optional[str],
    status_filter: Optional[str],
    sim_filter: Optional[str],
    source_job_id: Optional[UUID] = None,
) -> tuple[list[HubAssetResponse], dict[str, HubAssetDetailResponse], int]:
    vehicle_query = db.query(Vehicle).filter(Vehicle.hub_id == hub.id)
    if source_job_id:
        vehicle_query = vehicle_query.filter(Vehicle.source_job_id == source_job_id)
    if search:
        pattern = f"%{search.strip().lower()}%"
        vehicle_query = vehicle_query.filter(
            or_(
                func.lower(func.coalesce(Vehicle.asset_name, "")).like(pattern),
                func.lower(func.coalesce(Vehicle.asset_type, "")).like(pattern),
                func.lower(func.coalesce(Vehicle.license_plate, "")).like(pattern),
                func.lower(func.coalesce(Vehicle.vin, "")).like(pattern),
                func.lower(func.coalesce(Vehicle.make, "")).like(pattern),
                func.lower(func.coalesce(Vehicle.model, "")).like(pattern),
                func.lower(func.coalesce(Vehicle.notes, "")).like(pattern),
            )
        )
    if status_filter:
        vehicle_query = vehicle_query.filter(
            func.lower(func.cast(Vehicle.status, String)) == status_filter.strip().lower()
        )

    vehicles = vehicle_query.all()
    vehicle_ids = [vehicle.id for vehicle in vehicles]

    devices_by_vehicle: dict[UUID, list[HubAssetDeviceResponse]] = {}
    if vehicle_ids:
        assignment_rows = (
            db.query(HardwareAssignment, HardwareInventory, Vehicle)
            .join(HardwareInventory, HardwareInventory.id == HardwareAssignment.hardware_id)
            .join(Vehicle, Vehicle.id == HardwareAssignment.vehicle_id)
            .options(
                joinedload(HardwareInventory.assignments).joinedload(HardwareAssignment.vehicle).joinedload(Vehicle.hub),
                joinedload(HardwareInventory.assignments).joinedload(HardwareAssignment.hub),
                joinedload(HardwareInventory.assignments).joinedload(HardwareAssignment.assigned_user),
            )
            .filter(
                HardwareAssignment.is_active.is_(True),
                Vehicle.id.in_(vehicle_ids),
            )
            .order_by(HardwareAssignment.assigned_at.desc())
            .all()
        )
        for assignment, hardware, vehicle in assignment_rows:
            devices_by_vehicle.setdefault(vehicle.id, []).append(
                _serialize_assignment_device(assignment, hardware, vehicle)
            )

    detail_by_id: dict[str, HubAssetDetailResponse] = {}
    for vehicle in vehicles:
        detail = _serialize_vehicle_asset(hub, vehicle, devices_by_vehicle.get(vehicle.id, []))
        detail_by_id[detail.id] = detail

    for detail in _build_virtual_asset_details(db, hub, search=search, status_filter=status_filter):
        detail_by_id[detail.id] = detail

    all_details = list(detail_by_id.values())
    if sim_filter:
        normalized_filter = sim_filter.strip().lower()

        def matches_sim_filter(detail: HubAssetDetailResponse) -> bool:
            devices = detail.devices or []
            if normalized_filter == "with_sim":
                return any(device.sim for device in devices)
            if normalized_filter == "without_sim":
                return not any(device.sim for device in devices)
            if normalized_filter == "roaming":
                return any(device.sim and device.sim.roaming_enabled for device in devices)
            if normalized_filter == "attention":
                return any(
                    device.sim and (device.sim.status or "").lower() in {"suspended", "faulty"}
                    for device in devices
                )
            return True

        all_details = [detail for detail in all_details if matches_sim_filter(detail)]
    all_details.sort(
        key=lambda item: (
            (item.registration or item.label or "").strip().lower(),
            item.last_assignment_at or datetime.min.replace(tzinfo=timezone.utc),
        )
    )

    total = len(all_details)
    start = max((page - 1) * limit, 0)
    end = start + limit
    paged_details = all_details[start:end]
    return [_detail_to_summary(detail) for detail in paged_details], detail_by_id, total


def _require_hub_visibility(actor: User, hub: Hub, db: Session) -> None:
    if actor.role in {UserRole.admin, UserRole.technician}:
        return
    membership = (
        db.query(HubMembership)
        .filter(
            HubMembership.hub_id == hub.id,
            HubMembership.user_id == actor.id,
            HubMembership.status == HubMembershipStatus.active,
        )
        .first()
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions for this hub")


def _hub_subscription_days_left(db: Session, hub_id: UUID) -> int | None:
    today = datetime.now(timezone.utc).date()
    subscription = (
        db.query(Subscription)
        .filter(Subscription.hub_id == hub_id)
        .order_by(Subscription.is_active.desc(), Subscription.start_date.desc())
        .first()
    )
    if not subscription or not subscription.end_date:
        return None
    return int((subscription.end_date - today).days)


def _hub_subscription_window(db: Session, hub_id: UUID) -> tuple[str | None, str | None]:
    subscription = (
        db.query(Subscription)
        .filter(Subscription.hub_id == hub_id)
        .order_by(Subscription.is_active.desc(), Subscription.start_date.desc())
        .first()
    )
    if not subscription:
        return None, None
    start = subscription.start_date.isoformat() if subscription.start_date else None
    end = subscription.end_date.isoformat() if subscription.end_date else None
    return start, end


def _purge_expired_deleted_hubs(db: Session) -> int:
    now = datetime.now(timezone.utc)
    expired = (
        db.query(Hub)
        .filter(
            Hub.deleted_at.isnot(None),
            Hub.recycle_bin_expires_at.isnot(None),
            Hub.recycle_bin_expires_at <= now,
        )
        .all()
    )
    purged = 0
    for hub in expired:
        _delete_hub_with_dependencies(db, hub)
        purged += 1
    if purged:
        db.commit()
    return purged


def _soft_delete_hub(hub: Hub) -> None:
    now = datetime.now(timezone.utc)
    hub.deleted_at = now
    hub.recycle_bin_expires_at = now + timedelta(days=RECYCLE_RETENTION_DAYS)
    hub.status = "deleted"


@router.get("/")
async def list_hubs(
    search: Optional[str] = Query(default=None, min_length=1),
    tier: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    sort: str = Query(default="name_asc"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=25, ge=1, le=200),
    _: None = Depends(require_role(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    """List all hubs with subscription metadata."""
    _purge_expired_deleted_hubs(db)
    query = db.query(Hub).filter(Hub.deleted_at.is_(None))

    if search:
        like = f"%{search.strip().lower()}%"
        query = query.filter(
            (Hub.name.ilike(like)) | (Hub.code.ilike(like)) | (Hub.city.ilike(like)) | (Hub.country.ilike(like))
        )
    if tier:
        query = query.filter(Hub.subscription_tier.ilike(tier.strip()))
    if status_filter:
        query = query.filter(Hub.status.ilike(status_filter.strip()))

    total = query.count()

    if sort == "name_desc":
        query = query.order_by(Hub.name.desc())
    elif sort == "devices_desc":
        query = query.order_by(Hub.device_count.desc(), Hub.name.asc())
    elif sort == "devices_asc":
        query = query.order_by(Hub.device_count.asc(), Hub.name.asc())
    elif sort == "created_desc":
        query = query.order_by(Hub.created_at.desc())
    else:
        query = query.order_by(Hub.name.asc())

    hubs = query.offset((page - 1) * limit).limit(limit).all()
    hub_ids = [hub.id for hub in hubs]

    vehicle_counts: dict[UUID, int] = {}
    device_counts: dict[UUID, int] = {}

    if hub_ids:
        vehicle_rows = (
            db.query(Vehicle.hub_id, func.count(Vehicle.id))
            .filter(Vehicle.hub_id.in_(hub_ids))
            .group_by(Vehicle.hub_id)
            .all()
        )
        vehicle_counts = {hub_id: int(count) for hub_id, count in vehicle_rows}

        device_rows = (
            db.query(
                func.coalesce(HardwareAssignment.hub_id, Vehicle.hub_id),
                func.count(func.distinct(HardwareAssignment.hardware_id)),
            )
            .outerjoin(Vehicle, Vehicle.id == HardwareAssignment.vehicle_id)
            .filter(
                HardwareAssignment.is_active.is_(True),
                or_(
                    HardwareAssignment.hub_id.in_(hub_ids),
                    Vehicle.hub_id.in_(hub_ids),
                ),
            )
            .group_by(func.coalesce(HardwareAssignment.hub_id, Vehicle.hub_id))
            .all()
        )
        device_counts = {hub_id: int(count) for hub_id, count in device_rows if hub_id is not None}
    return {
        "data": [
            _serialize_hub(
                hub,
                device_count=device_counts.get(hub.id, 0),
                vehicle_count=vehicle_counts.get(hub.id, 0),
                subscription_days_left=_hub_subscription_days_left(db, hub.id),
            )
            for hub in hubs
        ],
        "meta": {
            "page": page,
            "per_page": limit,
            "total": total,
        },
    }


@router.get("/{hub_id:uuid}", response_model=HubResponse)
async def get_hub(
    hub_id: UUID,
    _: None = Depends(require_role(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    """Get a specific hub by ID."""
    hub = db.query(Hub).filter(Hub.id == hub_id).first()
    if not hub or hub.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hub not found")
    vehicle_count = db.query(func.count(Vehicle.id)).filter(Vehicle.hub_id == hub.id).scalar() or 0
    device_count = (
        db.query(func.count(func.distinct(HardwareAssignment.hardware_id)))
        .outerjoin(Vehicle, Vehicle.id == HardwareAssignment.vehicle_id)
        .filter(
            HardwareAssignment.is_active.is_(True),
            or_(
                HardwareAssignment.hub_id == hub.id,
                Vehicle.hub_id == hub.id,
            ),
        )
        .scalar()
        or 0
    )
    devices = _active_hub_devices(db, hub.id)
    start_date, end_date = _hub_subscription_window(db, hub.id)
    return _serialize_hub(
        hub,
        device_count=int(device_count),
        vehicle_count=int(vehicle_count),
        subscription_days_left=_hub_subscription_days_left(db, hub.id),
        subscription_start_date=start_date,
        subscription_end_date=end_date,
        devices=devices,
    )


@router.get("/{hub_id:uuid}/assets", response_model=HubAssetListResponse)
async def list_hub_assets(
    hub_id: UUID,
    search: Optional[str] = Query(default=None, min_length=1),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    sim_filter: Optional[str] = Query(default=None, alias="simFilter"),
    source_job_id: Optional[UUID] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    actor: User = Depends(require_role(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    """List assets registered under a hub with assigned-device counts."""
    hub = db.query(Hub).filter(Hub.id == hub_id).first()
    if not hub or hub.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hub not found")
    _require_hub_visibility(actor, hub, db)
    assets, _, total = _hub_asset_index_paginated(
        db,
        hub,
        page=page,
        limit=limit,
        search=search,
        status_filter=status_filter,
        sim_filter=sim_filter,
        source_job_id=source_job_id,
    )
    return HubAssetListResponse(
        data=HubAssetListData(items=assets),
        meta=HubAssetPaginationMeta(page=page, per_page=limit, total=total),
    )


@router.get("/{hub_id:uuid}/assets/options", response_model=HubAssetListResponse)
async def list_hub_asset_options(
    hub_id: UUID,
    search: Optional[str] = Query(default=None, min_length=1),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    actor: User = Depends(require_role(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    """Lightweight asset selector list for assignment workflows."""
    hub = db.query(Hub).filter(Hub.id == hub_id).first()
    if not hub or hub.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hub not found")
    _require_hub_visibility(actor, hub, db)

    vehicle_query = db.query(Vehicle).filter(Vehicle.hub_id == hub.id)
    if search:
        pattern = f"%{search.strip().lower()}%"
        vehicle_query = vehicle_query.filter(
            or_(
                func.lower(func.coalesce(Vehicle.asset_name, "")).like(pattern),
                func.lower(func.coalesce(Vehicle.asset_type, "")).like(pattern),
                func.lower(func.coalesce(Vehicle.license_plate, "")).like(pattern),
                func.lower(func.coalesce(Vehicle.vin, "")).like(pattern),
            )
        )
    if status_filter:
        vehicle_query = vehicle_query.filter(
            func.lower(func.cast(Vehicle.status, String)) == status_filter.strip().lower()
        )

    total = vehicle_query.count()
    vehicles = (
        vehicle_query.order_by(Vehicle.updated_at.desc(), Vehicle.created_at.desc())
        .offset(max((page - 1) * limit, 0))
        .limit(limit)
        .all()
    )
    vehicle_ids = [vehicle.id for vehicle in vehicles]
    assignment_counts: dict[UUID, int] = {}
    last_assigned_at: dict[UUID, datetime] = {}
    if vehicle_ids:
        assignment_rows = (
            db.query(
                HardwareAssignment.vehicle_id,
                func.count(HardwareAssignment.id),
                func.max(func.coalesce(HardwareAssignment.installed_at, HardwareAssignment.assigned_at)),
            )
            .filter(
                HardwareAssignment.vehicle_id.in_(vehicle_ids),
                HardwareAssignment.is_active.is_(True),
            )
            .group_by(HardwareAssignment.vehicle_id)
            .all()
        )
        for vehicle_id, count, max_assigned in assignment_rows:
            if vehicle_id is None:
                continue
            assignment_counts[vehicle_id] = int(count or 0)
            if max_assigned is not None:
                last_assigned_at[vehicle_id] = max_assigned

    items = [
        HubAssetResponse(
            id=str(vehicle.id),
            asset_type=vehicle.asset_type,
            asset_name=vehicle.asset_name,
            asset_type_other=vehicle.asset_type_other,
            registration=vehicle.license_plate,
            label=vehicle.asset_name or vehicle.model or vehicle.make or vehicle.vin or vehicle.license_plate,
            vin=vehicle.vin,
            make=vehicle.make,
            model=vehicle.model,
            year=vehicle.year,
            color=vehicle.color,
            engine_capacity=vehicle.engine_capacity,
            co2_emissions=vehicle.co2_emissions,
            fuel_type=vehicle.fuel_type,
            status=vehicle.status,
            notes=vehicle.notes,
            tracking_state="tracked" if assignment_counts.get(vehicle.id, 0) > 0 else "unassigned",
            source_job_id=str(vehicle.source_job_id) if vehicle.source_job_id else None,
            assigned_device_count=assignment_counts.get(vehicle.id, 0),
            last_assignment_at=last_assigned_at.get(vehicle.id),
        )
        for vehicle in vehicles
    ]
    return HubAssetListResponse(
        data=HubAssetListData(items=items),
        meta=HubAssetPaginationMeta(page=page, per_page=limit, total=total),
    )


@router.get("/{hub_id:uuid}/assets/{asset_id}", response_model=HubAssetDetailResponse)
async def get_hub_asset(
    hub_id: UUID,
    asset_id: str,
    actor: User = Depends(require_role(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    """Return one hub asset plus its active device assignments."""
    hub = db.query(Hub).filter(Hub.id == hub_id).first()
    if not hub or hub.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hub not found")
    _require_hub_visibility(actor, hub, db)

    _, detail_by_id, _ = _hub_asset_index_paginated(
        db,
        hub,
        page=1,
        limit=100000,
        search=None,
        status_filter=None,
        sim_filter=None,
        source_job_id=None,
    )
    detail = detail_by_id.get(str(asset_id))
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return detail


@router.patch("/{hub_id:uuid}/assets/{asset_id}", response_model=HubAssetDetailResponse)
async def update_hub_asset(
    hub_id: UUID,
    asset_id: str,
    payload: HubAssetUpdate,
    actor: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    """Update admin-maintained asset metadata for a hub asset."""
    hub = db.query(Hub).filter(Hub.id == hub_id).first()
    if not hub or hub.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hub not found")

    if str(asset_id).startswith("virtual:"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment-only asset records cannot be edited until a formal asset exists",
        )

    try:
        asset_uuid = UUID(str(asset_id))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid asset ID") from exc

    asset = db.query(Vehicle).filter(Vehicle.id == asset_uuid, Vehicle.hub_id == hub.id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    changed_fields: list[str] = []

    def _apply(field_name: str, value, attr_name: str | None = None):
        nonlocal changed_fields
        if value is None:
            return
        target_attr = attr_name or field_name
        cleaned = _clean_text(value)
        current = getattr(asset, target_attr)
        if cleaned != current:
            setattr(asset, target_attr, cleaned)
            changed_fields.append(field_name)

    _apply("asset_type", payload.asset_type)
    _apply("asset_name", payload.asset_name)
    _apply("asset_type_other", payload.asset_type_other)
    _apply("registration", payload.registration, "license_plate")
    _apply("vin", payload.vin)
    _apply("make", payload.make)
    _apply("model", payload.model)
    _apply("year", payload.year)
    _apply("color", payload.color)
    _apply("engine_capacity", payload.engine_capacity)
    _apply("co2_emissions", payload.co2_emissions)
    _apply("fuel_type", payload.fuel_type)
    if payload.notes is not None and _clean_text(payload.notes) != asset.notes:
        asset.notes = _clean_text(payload.notes)
        changed_fields.append("notes")

    db.add(asset)
    db.commit()
    db.refresh(asset)

    append_admin_activity(
        db,
        module="assets",
        change="Asset updated",
        details=f"{hub.code} · {asset.asset_name or asset.license_plate or asset.id} · {', '.join(changed_fields) if changed_fields else 'no field changes'}",
        actor=actor,
        target_type="asset",
        target_id=str(asset.id),
    )

    _, detail_by_id, _ = _hub_asset_index(db, hub)
    detail = detail_by_id.get(str(asset.id))
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found after update")
    return detail


@router.post("/{hub_id:uuid}/assets", response_model=HubAssetDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_hub_asset(
    hub_id: UUID,
    payload: HubAssetCreate,
    actor: User = Depends(require_role(UserRole.technician)),
    db: Session = Depends(get_db),
):
    """Create a new asset under a hub and optionally assign available hardware."""
    hub = db.query(Hub).filter(Hub.id == hub_id).first()
    if not hub or hub.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hub not found")
    _require_hub_visibility(actor, hub, db)

    if not payload.source_job_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Asset capture must be linked to a technician job card",
        )

    try:
        source_job_uuid = UUID(payload.source_job_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid source job ID") from exc

    source_job = (
        db.query(TechnicianJob)
        .filter(TechnicianJob.id == source_job_uuid)
        .first()
    )
    if not source_job or source_job.hub_id != hub.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Technician job not found for this hub")
    if source_job.assigned_technician_id != actor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assigned technician can capture assets for this job",
        )
    if source_job.status not in {TechnicianJobStatus.assigned, TechnicianJobStatus.in_progress}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assets can only be captured while the job is active",
        )

    asset = Vehicle(
        hub_id=hub.id,
        asset_type=_clean_text(payload.asset_type) or "other",
        asset_name=_clean_text(payload.asset_name) or "Unnamed asset",
        asset_type_other=_clean_text(payload.asset_type_other),
        license_plate=_clean_text(payload.registration),
        vin=_clean_text(payload.vin),
        make=_clean_text(payload.make),
        model=_clean_text(payload.model),
        year=_clean_text(payload.year),
        color=_clean_text(payload.color),
        engine_capacity=_clean_text(payload.engine_capacity),
        co2_emissions=_clean_text(payload.co2_emissions),
        fuel_type=_clean_text(payload.fuel_type),
        notes=_clean_text(payload.notes),
        source_job_id=source_job_uuid,
    )
    db.add(asset)
    db.flush()

    requested_pairs = payload.hardware_assignments or [
        {"hardware_id": hardware_id, "sim_id": None} for hardware_id in payload.hardware_ids
    ]

    for pair in requested_pairs:
        hardware_id = int(pair.hardware_id if hasattr(pair, "hardware_id") else pair.get("hardware_id"))
        sim_id = pair.sim_id if hasattr(pair, "sim_id") else pair.get("sim_id")
        hardware = db.query(HardwareInventory).filter(HardwareInventory.id == hardware_id).first()
        if not hardware:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Hardware {hardware_id} not found")
        if hardware.status not in {HardwareStatus.IN_STOCK, HardwareStatus.MAINTENANCE}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Hardware {hardware.imei} is not available for assignment",
            )
        assign_hardware_to_vehicle(
            db,
            imei=hardware.imei,
            vehicle_id=asset.id,
            hub_id=hub.id,
            hardware_type=hardware.hardware_type,
            model=hardware.model,
            assigned_by=actor.id,
            requested_by=actor.id,
            technician=actor.name or actor.email,
            asset_label=asset.asset_name,
            asset_registration=asset.license_plate,
            notes=payload.notes,
        )
        if sim_id:
            sim = db.query(SimInventory).filter(SimInventory.id == sim_id).first()
            if not sim:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"SIM {sim_id} not found")
            if sim.status != SimStatus.IN_STOCK:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"SIM {sim.iccid} is not available for assignment",
                )
            _assign_sim_to_hardware(
                db,
                sim=sim,
                hardware=hardware,
                hub_id=hub.id,
                vehicle_id=asset.id,
                notes=f"Assigned during technician asset capture for {asset.asset_name}",
            )

    db.commit()
    append_admin_activity(
        db,
        module="assets",
        change="Asset created",
        details=f"{hub.code} · {asset.asset_name} · hardware {len(payload.hardware_ids)}",
        actor=actor,
        target_type="asset",
        target_id=str(asset.id),
    )

    _, detail_by_id, _ = _hub_asset_index_paginated(
        db,
        hub,
        page=1,
        limit=100000,
        search=None,
        status_filter=None,
        sim_filter=None,
    )
    detail = detail_by_id.get(str(asset.id))
    if not detail:
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Asset created but could not be loaded")
    return detail


@router.get("/current/summary")
async def get_current_hub_summary(
    context: HubAccessContext = Depends(
        require_hub_access(
            UserRole.admin,
            UserRole.technician,
            UserRole.company,
            UserRole.client,
        )
    ),
    db: Session = Depends(get_db),
):
    """Return dashboard summary for the currently scoped hub."""
    if context.hub is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Hub-ID header is required to load hub summary",
        )

    hub = context.hub
    if hub.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hub not found")
    today = datetime.now(timezone.utc).date()

    active_subscription = (
        db.query(Subscription)
        .filter(Subscription.hub_id == hub.id, Subscription.is_active.is_(True))
        .order_by(Subscription.start_date.desc())
        .first()
    )
    latest_subscription = active_subscription or (
        db.query(Subscription)
        .filter(Subscription.hub_id == hub.id)
        .order_by(Subscription.start_date.desc())
        .first()
    )

    days_left = None
    if latest_subscription and latest_subscription.end_date:
        days_left = (latest_subscription.end_date - today).days
    subscription_status = _normalize_subscription_status(hub.status)

    membership_role = context.membership.role if context.membership else context.user.role
    role_value = membership_role.value if hasattr(membership_role, "value") else str(membership_role)

    active_users = (
        db.query(func.count(HubMembership.id))
        .filter(
            HubMembership.hub_id == hub.id,
            HubMembership.status == HubMembershipStatus.active,
        )
        .scalar()
        or 0
    )
    vehicle_count = db.query(func.count(Vehicle.id)).filter(Vehicle.hub_id == hub.id).scalar() or 0
    assigned_assets = (
        db.query(func.count(func.distinct(HardwareAssignment.hardware_id)))
        .outerjoin(Vehicle, Vehicle.id == HardwareAssignment.vehicle_id)
        .filter(
            HardwareAssignment.is_active.is_(True),
            or_(
                HardwareAssignment.hub_id == hub.id,
                Vehicle.hub_id == hub.id,
            ),
        )
        .scalar()
        or 0
    )
    active_devices = (
        db.query(func.count(HardwareInventory.id))
        .join(HardwareAssignment, HardwareAssignment.hardware_id == HardwareInventory.id)
        .outerjoin(Vehicle, Vehicle.id == HardwareAssignment.vehicle_id)
        .filter(
            HardwareAssignment.is_active.is_(True),
            or_(
                HardwareAssignment.hub_id == hub.id,
                Vehicle.hub_id == hub.id,
            ),
            HardwareInventory.status.in_([HardwareStatus.ACTIVE, HardwareStatus.ASSIGNED]),
        )
        .scalar()
        or 0
    )

    role_features = {
        UserRole.admin.value: ["billing_manage", "users_manage", "assets_manage", "support_manage"],
        UserRole.company.value: ["billing_view", "users_manage", "assets_view", "support_manage"],
        UserRole.technician.value: ["assets_manage", "support_manage", "diagnostics"],
        UserRole.client.value: ["billing_view", "assets_view", "support_request"],
    }

    return {
        "hub": {
            "id": str(hub.id),
            "name": hub.name,
            "code": hub.code,
            "type": hub.hub_type or "company",
            "status": hub.status or "active",
            "tier": hub.subscription_tier or "individual",
            "timezone": hub.timezone,
            "location": {
                "country": hub.country,
                "city": hub.city,
                "address": hub.address_line,
            },
        },
        "subscription": {
            "status": subscription_status,
            "tier": _normalize_subscription_tier(
                hub.subscription_tier or (latest_subscription.tier if latest_subscription else "individual"),
                hub.hub_type,
            ),
            "start_date": latest_subscription.start_date.isoformat() if latest_subscription and latest_subscription.start_date else None,
            "end_date": latest_subscription.end_date.isoformat() if latest_subscription and latest_subscription.end_date else None,
            "days_left": days_left,
            "billing_cycle": hub.billing_cycle or "monthly",
        },
        "metrics": {
            "active_users": int(active_users),
            "assets": int(assigned_assets),
            "active_devices": int(active_devices),
            "vehicles": int(vehicle_count),
        },
        "viewer": {
            "role": role_value,
            "features": role_features.get(role_value, role_features[UserRole.client.value]),
        },
    }


@router.get("/current/assets", response_model=HubAssetListResponse)
async def list_current_hub_assets(
    search: Optional[str] = Query(default=None, min_length=1),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    sim_filter: Optional[str] = Query(default=None, alias="simFilter"),
    source_job_id: Optional[UUID] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    context: HubAccessContext = Depends(
        require_hub_access(
            UserRole.admin,
            UserRole.technician,
            UserRole.company,
            UserRole.client,
        )
    ),
    db: Session = Depends(get_db),
):
    """List assets for the currently selected hub."""
    if context.hub is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Hub-ID header is required")
    hub = context.hub
    if hub.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hub not found")
    assets, _, total = _hub_asset_index_paginated(
        db,
        hub,
        page=page,
        limit=limit,
        search=search,
        status_filter=status_filter,
        sim_filter=sim_filter,
        source_job_id=source_job_id,
    )
    return HubAssetListResponse(
        data=HubAssetListData(items=assets),
        meta=HubAssetPaginationMeta(page=page, per_page=limit, total=total),
    )


@router.get("/current/assets/{asset_id}", response_model=HubAssetDetailResponse)
async def get_current_hub_asset(
    asset_id: str,
    context: HubAccessContext = Depends(
        require_hub_access(
            UserRole.admin,
            UserRole.technician,
            UserRole.company,
            UserRole.client,
        )
    ),
    db: Session = Depends(get_db),
):
    """Return one asset with assigned devices for the currently selected hub."""
    if context.hub is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Hub-ID header is required")
    hub = context.hub
    if hub.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hub not found")

    _, detail_by_id, _ = _hub_asset_index_paginated(
        db,
        hub,
        page=1,
        limit=100000,
        search=None,
        status_filter=None,
        sim_filter=None,
    )
    detail = detail_by_id.get(str(asset_id))
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return detail


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _delete_hub_with_dependencies(db: Session, hub: Hub) -> None:
    vehicle_ids = [row[0] for row in db.query(Vehicle.id).filter(Vehicle.hub_id == hub.id).all()]
    if vehicle_ids:
        db.query(Device).filter(Device.vehicle_id.in_(vehicle_ids)).update(
            {Device.vehicle_id: None},
            synchronize_session=False,
        )
        db.query(HardwareAssignment).filter(HardwareAssignment.vehicle_id.in_(vehicle_ids)).delete(
            synchronize_session=False
        )
        db.query(Vehicle).filter(Vehicle.id.in_(vehicle_ids)).delete(synchronize_session=False)

    db.query(HardwareAssignment).filter(HardwareAssignment.hub_id == hub.id).delete(synchronize_session=False)
    db.query(Technician).filter(Technician.hub_id == hub.id).delete(synchronize_session=False)
    db.query(Subscription).filter(Subscription.hub_id == hub.id).delete(synchronize_session=False)
    db.query(HubMembership).filter(HubMembership.hub_id == hub.id).delete(synchronize_session=False)
    db.delete(hub)


@router.post("/", response_model=HubResponse, status_code=status.HTTP_201_CREATED)
async def create_hub(
    payload: HubCreate,
    user: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    """Provision a hub with subscription + billing metadata stored in description."""
    desired_code = payload.hub_code or payload.hub_name
    code = _resolve_unique_code(db, desired_code, fallback_name=payload.hub_name)
    normalized_hub_type = _normalize_hub_type(payload.hub_type)
    tier = _tier_from_hub_type(normalized_hub_type)

    hub = Hub(
        name=payload.hub_name,
        code=code,
        location=payload.city or payload.country,
        timezone=payload.timezone,
        owner_id=user.id,
        hub_type=normalized_hub_type,
        subscription_tier=_normalize_subscription_tier(tier, normalized_hub_type),
        payment_method=payload.payment_method,
        billing_cycle=payload.billing_cycle,
        status="active",
        country=payload.country,
        city=payload.city,
        address_line=payload.address_line,
        currency=payload.currency,
        go_live_date=_parse_date(payload.go_live_date),
        notes=payload.notes,
        primary_contact_name=payload.primary_contact_name,
        primary_contact_email=payload.primary_contact_email,
        primary_contact_phone=payload.primary_contact_phone,
        billing_contact_name=payload.billing_contact_name,
        billing_contact_email=payload.billing_contact_email,
        billing_contact_phone=payload.billing_contact_phone,
    )

    db.add(hub)
    db.flush()

    # Attach requested operators as memberships (create user if needed)
    for operator in payload.users:
        normalized_role = str(operator.role).lower().strip()
        try:
            operator_role = UserRole(normalized_role)
        except ValueError:
            operator_role = UserRole.client

        db_user = db.query(User).filter(User.email == operator.email).one_or_none()
        if not db_user:
            if not operator.password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Password is required for new user {operator.email}",
                )
            db_user = User(
                name=operator.name,
                email=operator.email,
                hashed_password=get_password_hash(operator.password),
                role=operator_role,
                is_active=True,
                is_verified=True,
            )
            db.add(db_user)
            db.flush()
        elif operator.password:
            db_user.hashed_password = get_password_hash(operator.password)
            db_user.is_active = True
        _enforce_admin_role_protection(db_user, operator_role)
        db_user.role = operator_role
        membership = (
            db.query(HubMembership)
            .filter(HubMembership.hub_id == hub.id, HubMembership.user_id == db_user.id)
            .one_or_none()
        )
        if not membership:
            membership = HubMembership(
                hub_id=hub.id,
                user_id=db_user.id,
                role=operator_role,
                status=HubMembershipStatus.active,
                is_primary=False,
            )
            db.add(membership)
        else:
            membership.role = operator_role
            membership.status = HubMembershipStatus.active

    db.commit()
    db.refresh(hub)
    append_admin_activity(
        db,
        module="hubs",
        change="Hub created",
        details=f"{hub.name} ({hub.code}) provisioned",
        actor=user,
        target_type="hub",
        target_id=str(hub.id),
    )
    vehicle_count = db.query(func.count(Vehicle.id)).filter(Vehicle.hub_id == hub.id).scalar() or 0
    device_count = (
        db.query(func.count(func.distinct(HardwareAssignment.hardware_id)))
        .outerjoin(Vehicle, Vehicle.id == HardwareAssignment.vehicle_id)
        .filter(
            HardwareAssignment.is_active.is_(True),
            or_(
                HardwareAssignment.hub_id == hub.id,
                Vehicle.hub_id == hub.id,
            ),
        )
        .scalar()
        or 0
    )
    start_date, end_date = _hub_subscription_window(db, hub.id)
    return _serialize_hub(
        hub,
        device_count=int(device_count),
        vehicle_count=int(vehicle_count),
        subscription_days_left=_hub_subscription_days_left(db, hub.id),
        subscription_start_date=start_date,
        subscription_end_date=end_date,
    )


@router.get("/recycle-bin/items")
async def list_recycle_bin(
    _: None = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    """List hubs currently in recycle bin."""
    _purge_expired_deleted_hubs(db)
    rows = (
        db.query(Hub)
        .filter(Hub.deleted_at.isnot(None), Hub.recycle_bin_expires_at.isnot(None))
        .order_by(Hub.deleted_at.desc())
        .all()
    )
    now = datetime.now(timezone.utc)
    return {
        "items": [
            {
                "id": str(hub.id),
                "name": hub.name,
                "code": hub.code,
                "deleted_at": hub.deleted_at.isoformat() if hub.deleted_at else None,
                "recycle_bin_expires_at": hub.recycle_bin_expires_at.isoformat() if hub.recycle_bin_expires_at else None,
                "days_until_purge": (
                    max(0, int((hub.recycle_bin_expires_at - now).total_seconds() // 86400))
                    if hub.recycle_bin_expires_at
                    else None
                ),
            }
            for hub in rows
        ]
    }


@router.post("/{hub_id}/restore", response_model=HubResponse)
async def restore_hub(
    hub_id: str,
    actor: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    """Restore a hub from recycle bin."""
    try:
        hub_uuid = UUID(str(hub_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid hub id")

    hub = db.query(Hub).filter(Hub.id == hub_uuid).first()
    if not hub or hub.deleted_at is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hub not found in recycle bin")

    hub.deleted_at = None
    hub.recycle_bin_expires_at = None
    hub.status = "active"
    db.commit()
    db.refresh(hub)
    append_admin_activity(
        db,
        module="hubs",
        change="Hub restored from recycle bin",
        details=f"{hub.name} ({hub.code}) restored",
        actor=actor,
        target_type="hub",
        target_id=str(hub.id),
    )

    vehicle_count = db.query(func.count(Vehicle.id)).filter(Vehicle.hub_id == hub.id).scalar() or 0
    device_count = (
        db.query(func.count(func.distinct(HardwareAssignment.hardware_id)))
        .outerjoin(Vehicle, Vehicle.id == HardwareAssignment.vehicle_id)
        .filter(
            HardwareAssignment.is_active.is_(True),
            or_(HardwareAssignment.hub_id == hub.id, Vehicle.hub_id == hub.id),
        )
        .scalar()
        or 0
    )
    start_date, end_date = _hub_subscription_window(db, hub.id)
    return _serialize_hub(
        hub,
        device_count=int(device_count),
        vehicle_count=int(vehicle_count),
        subscription_days_left=_hub_subscription_days_left(db, hub.id),
        subscription_start_date=start_date,
        subscription_end_date=end_date,
    )


@router.delete("/{hub_id}/purge", status_code=status.HTTP_204_NO_CONTENT)
async def purge_hub(
    hub_id: str,
    actor: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    """Permanently delete a hub currently in recycle bin."""
    try:
        hub_uuid = UUID(str(hub_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid hub id")

    hub = db.query(Hub).filter(Hub.id == hub_uuid).first()
    if not hub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hub not found")
    if hub.deleted_at is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hub is not in recycle bin")

    hub_name = hub.name
    hub_code = hub.code
    _delete_hub_with_dependencies(db, hub)
    db.commit()
    append_admin_activity(
        db,
        module="hubs",
        change="Hub permanently deleted",
        details=f"{hub_name} ({hub_code}) permanently deleted from recycle bin",
        actor=actor,
        target_type="hub",
        target_id=str(hub_uuid),
    )
    return None


@router.delete("/{hub_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hub(
    hub_id: str,
    actor: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    """Delete a hub and related hub-scoped records."""
    try:
        hub_uuid = UUID(str(hub_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid hub id")

    hub = db.query(Hub).filter(Hub.id == hub_uuid).first()
    if not hub or hub.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hub not found")

    hub_name = hub.name
    hub_code = hub.code
    _soft_delete_hub(hub)
    db.commit()
    append_admin_activity(
        db,
        module="hubs",
        change="Hub moved to recycle bin",
        details=f"{hub_name} ({hub_code}) moved to recycle bin ({RECYCLE_RETENTION_DAYS} days)",
        actor=actor,
        target_type="hub",
        target_id=str(hub_uuid),
    )
    return None


@router.post("/bulk-delete")
async def bulk_delete_hubs(
    payload: HubBulkDeleteRequest,
    actor: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    """Delete multiple hubs in one operation."""
    ids: list[UUID] = []
    raw_codes: list[str] = []
    for raw_id in payload.hub_ids:
        try:
            ids.append(UUID(str(raw_id)))
        except ValueError:
            if raw_id:
                raw_codes.append(str(raw_id).strip())

    if not ids and not raw_codes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid hub ids provided")

    hubs_query = db.query(Hub)
    predicates = []
    if ids:
        predicates.append(Hub.id.in_(ids))
    if raw_codes:
        predicates.append(Hub.code.in_(raw_codes))
    hubs = hubs_query.filter(or_(*predicates), Hub.deleted_at.is_(None)).all()
    if not hubs:
        return {"deleted": 0, "requested": len(payload.hub_ids), "deleted_ids": [], "not_found": payload.hub_ids}

    deleted_count = 0
    deleted_ids: list[str] = []
    for hub in hubs:
        hub_id = hub.id
        hub_name = hub.name
        hub_code = hub.code
        _soft_delete_hub(hub)
        deleted_count += 1
        deleted_ids.append(str(hub_id))
        append_admin_activity(
            db,
            module="hubs",
            change="Hub moved to recycle bin",
            details=f"{hub_name} ({hub_code}) moved to recycle bin via bulk action ({RECYCLE_RETENTION_DAYS} days)",
            actor=actor,
            target_type="hub",
            target_id=str(hub_id),
        )

    db.commit()
    requested_set = {str(item).strip() for item in payload.hub_ids if str(item).strip()}
    matched_set = set(deleted_ids) | {hub.code for hub in hubs}
    not_found = sorted(requested_set - matched_set)
    return {
        "deleted": deleted_count,
        "requested": len(payload.hub_ids),
        "deleted_ids": deleted_ids,
        "not_found": not_found,
    }


@router.patch("/{hub_id}", response_model=HubResponse)
async def update_hub(
    hub_id: str,
    payload: HubUpdate,
    actor: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    """Update hub metadata used by the admin UI."""
    try:
        hub_uuid = UUID(str(hub_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid hub id")

    hub = db.query(Hub).filter(Hub.id == hub_uuid).first()
    if not hub or hub.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hub not found")

    # Keep persisted hub type/tier normalized to avoid enum/case drift from legacy records.
    hub.hub_type = _normalize_hub_type(hub.hub_type)
    hub.subscription_tier = _normalize_subscription_tier(hub.subscription_tier, hub.hub_type)

    payload_data = payload.model_dump(exclude_unset=True, by_alias=True)

    if payload.hub_name is not None:
        hub.name = payload.hub_name
    if payload.timezone is not None:
        hub.timezone = payload.timezone
    if payload.country is not None:
        hub.country = payload.country
    if payload.city is not None:
        hub.city = payload.city
    if payload.country is not None or payload.city is not None:
        hub.location = payload.city or payload.country or hub.location

    if payload.hub_type is not None:
        hub.hub_type = _normalize_hub_type(payload.hub_type)
        hub.subscription_tier = _tier_from_hub_type(hub.hub_type)
    elif payload.subscription_tier is not None:
        # Billing tier is derived from hub type by design.
        hub.subscription_tier = _tier_from_hub_type(hub.hub_type)
    if payload.payment_method is not None:
        hub.payment_method = payload.payment_method
    if payload.billing_cycle is not None:
        hub.billing_cycle = payload.billing_cycle
    if payload.status is not None:
        hub.status = _normalize_subscription_status(payload.status)
    if payload.address_line is not None:
        hub.address_line = payload.address_line
    if payload.go_live_date is not None:
        hub.go_live_date = _parse_date(payload.go_live_date) if payload.go_live_date else None
    if payload.notes is not None:
        hub.notes = payload.notes
    if payload.primary_contact_name is not None:
        hub.primary_contact_name = payload.primary_contact_name
    if payload.primary_contact_email is not None:
        hub.primary_contact_email = payload.primary_contact_email
    if payload.primary_contact_phone is not None:
        hub.primary_contact_phone = payload.primary_contact_phone
    if payload.billing_contact_name is not None:
        hub.billing_contact_name = payload.billing_contact_name
    if payload.billing_contact_email is not None:
        hub.billing_contact_email = payload.billing_contact_email
    if payload.billing_contact_phone is not None:
        hub.billing_contact_phone = payload.billing_contact_phone
    if payload.currency is not None:
        hub.currency = payload.currency

    changed_fields: list[str] = []
    if payload.hub_type is not None or payload.subscription_tier is not None:
        changed_fields.append(f"tier={hub.subscription_tier}")
    if payload.billing_cycle is not None:
        changed_fields.append(f"billing_cycle={hub.billing_cycle}")
    if payload.status is not None:
        changed_fields.append(f"status={hub.status}")
    subscription = (
        db.query(Subscription)
        .filter(Subscription.hub_id == hub.id)
        .order_by(Subscription.is_active.desc(), Subscription.start_date.desc())
        .first()
    )
    needs_subscription_update = (
        payload.days_left is not None
        or payload.subscription_start_date is not None
        or payload.subscription_end_date is not None
        or payload.status is not None
        or payload.hub_type is not None
        or payload.subscription_tier is not None
    )
    if needs_subscription_update:
        today = datetime.now(timezone.utc).date()
        if not subscription:
            subscription = Subscription(
                user_id=hub.owner_id,
                hub_id=hub.id,
                tier=_subscription_storage_tier(hub.subscription_tier, hub.hub_type),
                start_date=today,
                end_date=None,
                is_active=(hub.status or "").lower() == "active",
                auto_renew=False,
            )
            db.add(subscription)

        subscription.tier = _subscription_storage_tier(hub.subscription_tier, hub.hub_type)

        manual_start = _parse_date(payload.subscription_start_date) if payload.subscription_start_date else None
        manual_end = _parse_date(payload.subscription_end_date) if payload.subscription_end_date else None
        if payload.subscription_start_date is not None and payload.subscription_start_date and manual_start is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid subscription_start_date")
        if payload.subscription_end_date is not None and payload.subscription_end_date and manual_end is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid subscription_end_date")

        if manual_start is not None:
            subscription.start_date = manual_start
            changed_fields.append(f"start_date={manual_start.isoformat()}")

        if manual_end is not None:
            subscription.end_date = manual_end
            changed_fields.append(f"end_date={manual_end.isoformat()}")

        if payload.days_left is not None:
            base_start = manual_start or subscription.start_date or today
            subscription.start_date = base_start
            subscription.end_date = base_start + timedelta(days=int(payload.days_left))
            changed_fields.append(f"days_left={int(payload.days_left)}")

        if subscription.start_date and subscription.end_date and subscription.end_date < subscription.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="subscription_end_date cannot be before subscription_start_date",
            )

        if payload.status is not None:
            normalized_status = _normalize_subscription_status(payload.status)
            subscription.is_active = normalized_status == "active"

    db.add(hub)
    db.commit()
    db.refresh(hub)
    append_admin_activity(
        db,
        module="hubs",
        change="Hub billing/profile updated",
        details=(
            f"{hub.name} ({hub.code}) updated"
            + (f" [{', '.join(changed_fields)}]" if changed_fields else "")
        ),
        actor=actor,
        target_type="hub",
        target_id=str(hub.id),
    )
    vehicle_count = db.query(func.count(Vehicle.id)).filter(Vehicle.hub_id == hub.id).scalar() or 0
    device_count = (
        db.query(func.count(func.distinct(HardwareAssignment.hardware_id)))
        .outerjoin(Vehicle, Vehicle.id == HardwareAssignment.vehicle_id)
        .filter(
            HardwareAssignment.is_active.is_(True),
            or_(
                HardwareAssignment.hub_id == hub.id,
                Vehicle.hub_id == hub.id,
            ),
        )
        .scalar()
        or 0
    )
    start_date, end_date = _hub_subscription_window(db, hub.id)
    return _serialize_hub(
        hub,
        device_count=int(device_count),
        vehicle_count=int(vehicle_count),
        subscription_days_left=_hub_subscription_days_left(db, hub.id),
        subscription_start_date=start_date,
        subscription_end_date=end_date,
    )


@router.post("/{hub_id}/users", response_model=dict)
async def create_hub_user(
    hub_id: str,
    payload: HubUserCreate,
    actor: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    """Create (or reuse) a user and attach them to a hub as a membership."""
    try:
        hub_uuid = UUID(str(hub_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid hub id")

    hub = db.query(Hub).filter(Hub.id == hub_uuid).first()
    if not hub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hub not found")

    normalized_role = str(payload.role).lower().strip()
    try:
        role = UserRole(normalized_role)
    except ValueError:
        role = UserRole.client

    user = db.query(User).filter(User.email == payload.email).one_or_none()
    if not user:
        if not payload.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required when creating a new hub user",
            )
        user = User(
            name=payload.name,
            email=payload.email,
            hashed_password=get_password_hash(payload.password),
            role=role,
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.flush()
    elif payload.password:
        user.hashed_password = get_password_hash(payload.password)
        user.is_active = True
    _enforce_admin_role_protection(user, role)
    if payload.name:
        user.name = payload.name
    user.role = role

    membership = (
        db.query(HubMembership)
        .filter(HubMembership.hub_id == hub.id, HubMembership.user_id == user.id)
        .one_or_none()
    )
    if not membership:
        membership = HubMembership(
            hub_id=hub.id,
            user_id=user.id,
            role=role,
            status=HubMembershipStatus.active,
            is_primary=False,
        )
        db.add(membership)
    else:
        membership.role = role
        membership.status = HubMembershipStatus.active

    db.commit()
    db.refresh(user)
    append_admin_activity(
        db,
        module="access",
        change="Hub user assigned",
        details=f"{user.email} attached to {hub.code} as {role.value}",
        actor=actor,
        target_type="hub_user",
        target_id=str(user.id),
    )

    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
    }


@router.patch("/{hub_id}/users/{user_id}", response_model=dict)
async def update_hub_user(
    hub_id: str,
    user_id: str,
    payload: HubUserUpdate,
    actor: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    """Update an existing hub user's profile, role, and optional password."""
    try:
        hub_uuid = UUID(str(hub_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid hub id")
    try:
        user_uuid = UUID(str(user_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id")

    hub = db.query(Hub).filter(Hub.id == hub_uuid).first()
    if not hub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hub not found")

    membership = (
        db.query(HubMembership)
        .filter(HubMembership.hub_id == hub_uuid, HubMembership.user_id == user_uuid)
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hub user membership not found",
        )

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    changed_fields: list[str] = []

    if payload.name is not None:
        name_value = payload.name.strip()
        if name_value and name_value != user.name:
            changed_fields.append(f"name:{user.name}->{name_value}")
            user.name = name_value

    if payload.email is not None:
        email_value = payload.email.strip().lower()
        if _is_bootstrap_admin_email(user.email) and email_value != _normalize_email(user.email):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bootstrap admin email cannot be changed via hub access control",
            )
        if email_value and email_value != user.email.lower():
            email_exists = (
                db.query(User)
                .filter(func.lower(User.email) == email_value, User.id != user.id)
                .first()
            )
            if email_exists:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email is already in use",
                )
            changed_fields.append(f"email:{user.email}->{email_value}")
            user.email = email_value

    if payload.role is not None:
        normalized_role = payload.role.strip().lower()
        try:
            role = UserRole(normalized_role)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
        _enforce_admin_role_protection(user, role)
        if role != user.role:
            previous_role = user.role.value if hasattr(user.role, "value") else str(user.role)
            changed_fields.append(f"role:{previous_role}->{role.value}")
            user.role = role
            membership.role = role

    if payload.password:
        user.hashed_password = get_password_hash(payload.password)
        user.is_active = True
        changed_fields.append("password:reset")

    if not changed_fields:
        return {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        }

    db.add(user)
    db.add(membership)
    db.commit()
    db.refresh(user)
    append_admin_activity(
        db,
        module="access",
        change="Hub user updated",
        details=f"{user.email} in {hub.code} [{', '.join(changed_fields)}]",
        actor=actor,
        target_type="hub_user",
        target_id=str(user.id),
    )

    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
    }
