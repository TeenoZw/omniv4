"""Admin analytics routes."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.auth import require_role
from app.core.database import get_db
from app.models.enquiry import Enquiry, EnquiryStatus
from app.models.hardware import HardwareAssignment, HardwareInventory, HardwareStatus, SimInventory, SimStatus
from app.models.hub import Hub
from app.models.hub_membership import HubMembership, HubMembershipStatus
from app.models.subscription import Subscription
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle
from app.models.admin_activity import AdminActivityLog
from app.services.admin_activity import verify_admin_activity_integrity

router = APIRouter(prefix="/admin", tags=["admin"])


def _to_str(value: Any) -> str:
    return str(value) if value is not None else ""


def _parse_activity_details(raw: str | None) -> tuple[str | None, dict[str, Any] | None]:
    if not raw:
        return raw, None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return raw, None
    if not isinstance(payload, dict):
        return raw, None
    message = payload.get("message")
    details_message = message if isinstance(message, str) and message.strip() else raw
    details_meta = {key: value for key, value in payload.items() if key != "message"}
    return details_message, details_meta or None


def _build_public_stats(db: Session) -> dict[str, int]:
    active_users = (
        db.query(func.count(User.id))
        .filter(User.is_active.is_(True))
        .scalar()
        or 0
    )
    active_assets = (
        db.query(func.count(HardwareInventory.id))
        .filter(
            HardwareInventory.status.in_(
                [HardwareStatus.ACTIVE, HardwareStatus.ASSIGNED]
            )
        )
        .scalar()
        or 0
    )
    provinces_served = (
        db.query(func.count(func.distinct(Hub.city)))
        .filter(Hub.deleted_at.is_(None), Hub.city.isnot(None), Hub.city != "")
        .scalar()
        or 0
    )
    total_hubs = db.query(func.count(Hub.id)).filter(Hub.deleted_at.is_(None)).scalar() or 0

    return {
        "active_users": int(active_users),
        "active_assets": int(active_assets),
        "provinces_served": int(provinces_served),
        "total_hubs": int(total_hubs),
    }


@router.get("/activity")
async def activity_feed(
    limit: int = Query(default=50, ge=1, le=300),
    _: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    """Unified immutable activity feed for admin operations."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    rows = (
        db.query(AdminActivityLog)
        .filter(AdminActivityLog.created_at >= cutoff)
        .order_by(AdminActivityLog.created_at.desc())
        .limit(limit)
        .all()
    )
    items = []
    for row in rows:
        details_message, details_meta = _parse_activity_details(row.details)
        timestamp = row.created_at
        if timestamp is not None and timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        items.append(
            {
                "id": str(row.id),
                "sequence_no": row.sequence_no,
                "timestamp": timestamp.isoformat() if timestamp else None,
                "module": row.module,
                "change": row.change,
                "details": row.details,
                "details_message": details_message,
                "details_meta": details_meta,
                "user": row.actor_name or row.actor_email or "system",
                "user_email": row.actor_email,
                "target_type": row.target_type,
                "target_id": row.target_id,
                "entry_hash": row.entry_hash,
                "previous_hash": row.previous_hash,
            }
        )
    return {
        "items": items
    }


@router.get("/activity/integrity")
async def activity_integrity(
    limit: int = Query(default=500, ge=10, le=5000),
    _: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    """Verify integrity of append-only audit chain."""
    return verify_admin_activity_integrity(db, limit=limit)


@router.get("/stats/public")
async def public_stats(db: Session = Depends(get_db)):
    """Public-safe metrics for landing page counters."""
    return {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "metrics": _build_public_stats(db),
    }


@router.get("/stats")
async def admin_stats(
    _: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    """Admin analytics snapshot across hubs, users, devices, subscriptions, and enquiries."""
    hubs = (
        db.query(Hub)
        .options(joinedload(Hub.memberships).joinedload(HubMembership.user))
        .filter(Hub.deleted_at.is_(None))
        .all()
    )
    all_users = db.query(func.count(User.id)).scalar() or 0
    all_devices = db.query(func.count(HardwareInventory.id)).scalar() or 0
    active_subscriptions = (
        db.query(func.count(Subscription.id))
        .filter(Subscription.is_active.is_(True))
        .scalar()
        or 0
    )
    pending_enquiries = (
        db.query(func.count(Enquiry.id))
        .filter(Enquiry.status == EnquiryStatus.new)
        .scalar()
        or 0
    )
    onboarded_enquiries = (
        db.query(func.count(Enquiry.id))
        .filter(Enquiry.status == EnquiryStatus.onboarded)
        .scalar()
        or 0
    )

    hub_ids = [hub.id for hub in hubs]
    live_device_counts: dict[Any, int] = {}
    if hub_ids:
        rows = (
            db.query(
                func.coalesce(HardwareAssignment.hub_id, Vehicle.hub_id),
                func.count(func.distinct(HardwareAssignment.hardware_id)),
            )
            .outerjoin(Vehicle, Vehicle.id == HardwareAssignment.vehicle_id)
            .filter(
                HardwareAssignment.is_active.is_(True),
                (HardwareAssignment.hub_id.in_(hub_ids)) | (Vehicle.hub_id.in_(hub_ids)),
            )
            .group_by(func.coalesce(HardwareAssignment.hub_id, Vehicle.hub_id))
            .all()
        )
        live_device_counts = {hub_id: int(count) for hub_id, count in rows if hub_id is not None}

    hierarchy = []
    for hub in hubs:
        active_members = [
            membership
            for membership in (hub.memberships or [])
            if _to_str(getattr(membership.status, "value", membership.status))
            in (HubMembershipStatus.active.value, HubMembershipStatus.invited.value)
        ]
        hierarchy.append(
            {
                "id": _to_str(hub.id),
                "name": hub.name,
                "code": hub.code,
                "tier": hub.subscription_tier or "individual",
                "status": hub.status or "active",
                "device_count": int(live_device_counts.get(hub.id, hub.device_count or 0)),
                "users": [
                    {
                        "id": _to_str(membership.user.id),
                        "name": membership.user.name,
                        "email": membership.user.email,
                        "role": _to_str(getattr(membership.role, "value", membership.role)),
                    }
                    for membership in active_members
                    if membership.user is not None
                ],
            }
        )

    device_status_rows = (
        db.query(HardwareInventory.status, func.count(HardwareInventory.id))
        .group_by(HardwareInventory.status)
        .all()
    )
    device_status = [
        {
            "id": _to_str(getattr(row_status, "value", row_status)),
            "count": int(count),
        }
        for row_status, count in device_status_rows
    ]

    total_sims = db.query(func.count(SimInventory.id)).scalar() or 0
    assigned_sims = (
        db.query(func.count(SimInventory.id))
        .filter(SimInventory.status == SimStatus.ASSIGNED)
        .scalar()
        or 0
    )
    roaming_enabled_sims = (
        db.query(func.count(SimInventory.id))
        .filter(SimInventory.roaming_enabled.is_(True))
        .scalar()
        or 0
    )
    suspended_or_faulty_sims = (
        db.query(func.count(SimInventory.id))
        .filter(SimInventory.status.in_([SimStatus.SUSPENDED, SimStatus.FAULTY]))
        .scalar()
        or 0
    )

    return {
        "metrics": {
            "hubs": int(len(hubs)),
            "devices": int(all_devices),
            "users": int(all_users),
            "active_subscriptions": int(active_subscriptions),
            "pending_enquiries": int(pending_enquiries),
            "onboarded_enquiries": int(onboarded_enquiries),
            "sims": int(total_sims),
            "assigned_sims": int(assigned_sims),
            "roaming_enabled_sims": int(roaming_enabled_sims),
            "attention_sims": int(suspended_or_faulty_sims),
            **_build_public_stats(db),
        },
        "hierarchy": hierarchy,
        "device_status": device_status,
    }
