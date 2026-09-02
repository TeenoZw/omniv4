"""Customer onboarding enquiry routes."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import require_role
from app.core.email import get_admin_recipients, send_email
from app.core.database import get_db
from app.models.enquiry import Enquiry, EnquiryStatus, CustomerType
from app.models.user import UserRole
from app.schemas.enquiries import EnquiryCreate, EnquiryResponse, EnquiryUpdate
from app.models.user import User
from app.services.admin_activity import append_admin_activity

router = APIRouter()


def _serialize(enquiry: Enquiry) -> EnquiryResponse:
    return EnquiryResponse.model_validate(enquiry)


@router.post("/", response_model=EnquiryResponse, status_code=status.HTTP_201_CREATED)
async def create_enquiry(
    payload: EnquiryCreate,
    db: Session = Depends(get_db),
):
    """Create a new onboarding enquiry."""
    if not payload.terms_accepted or not payload.privacy_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Terms and privacy acceptance are required.",
        )

    enquiry = Enquiry(
        status=EnquiryStatus.new,
        customer_type=CustomerType(payload.customer_type),
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        company_name=payload.company_name,
        fleet_size=payload.fleet_size,
        operating_area=payload.operating_area,
        preferred_contact_method=payload.preferred_contact_method,
        expected_go_live_date=payload.expected_go_live_date,
        tracking_use_case=payload.tracking_use_case,
        hardware_choices=payload.hardware_choices,
        add_ons=payload.add_ons,
        message=payload.message,
        terms_accepted=payload.terms_accepted,
        privacy_accepted=payload.privacy_accepted,
    )

    db.add(enquiry)
    db.commit()
    db.refresh(enquiry)
    append_admin_activity(
        db,
        module="onboarding",
        change="Enquiry submitted",
        details=f"{enquiry.full_name} ({enquiry.customer_type.value}) submitted enquiry",
        actor_name=enquiry.full_name,
        actor_email=enquiry.email,
        target_type="enquiry",
        target_id=str(enquiry.id),
    )

    recipients = get_admin_recipients()
    if recipients:
        subject = f"New Omni Logistics enquiry: {enquiry.full_name}"
        body_lines = [
            f"Customer type: {enquiry.customer_type}",
            f"Name: {enquiry.full_name}",
            f"Email: {enquiry.email}",
            f"Phone: {enquiry.phone}",
            f"Company: {enquiry.company_name or '-'}",
            f"Fleet size: {enquiry.fleet_size or '-'}",
            f"Operating area: {enquiry.operating_area or '-'}",
            f"Preferred contact: {enquiry.preferred_contact_method or '-'}",
            f"Expected go-live: {enquiry.expected_go_live_date.isoformat() if enquiry.expected_go_live_date else '-'}",
            f"Use case: {enquiry.tracking_use_case or '-'}",
            f"Hardware: {', '.join(enquiry.hardware_choices or [])}",
            f"Add-ons: {', '.join(enquiry.add_ons or [])}",
            f"Message: {enquiry.message or '-'}",
            f"Submitted: {enquiry.created_at.isoformat()}",
        ]
        try:
            send_email(subject, "\n".join(body_lines), recipients=recipients)
        except Exception:
            # Avoid breaking enquiry creation if email fails.
            pass

    return _serialize(enquiry)


@router.get("/", response_model=list[EnquiryResponse])
async def list_enquiries(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    _: None = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    """List all enquiries for admin follow-up."""
    query = db.query(Enquiry)
    if status_filter:
        try:
            query = query.filter(Enquiry.status == EnquiryStatus(status_filter))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status filter")
    enquiries = query.order_by(Enquiry.created_at.desc()).all()
    return [_serialize(enquiry) for enquiry in enquiries]


@router.patch("/{enquiry_id}", response_model=EnquiryResponse)
async def update_enquiry(
    enquiry_id: str,
    payload: EnquiryUpdate,
    actor: User = Depends(require_role(UserRole.admin)),
    db: Session = Depends(get_db),
):
    """Update enquiry status, quotation, and admin notes."""
    enquiry = db.query(Enquiry).filter(Enquiry.id == enquiry_id).first()
    if not enquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enquiry not found")

    data = payload.model_dump(exclude_unset=True)
    if data.get("status") is not None:
        enquiry.status = EnquiryStatus(data["status"])
    if data.get("quoted_monthly") is not None:
        enquiry.quoted_monthly = data["quoted_monthly"]
    if data.get("quoted_hardware_total") is not None:
        enquiry.quoted_hardware_total = data["quoted_hardware_total"]
    if data.get("quote_sent_at") is not None:
        enquiry.quote_sent_at = data["quote_sent_at"]
        enquiry.responded_at = data["quote_sent_at"]
    if data.get("responded_at") is not None:
        enquiry.responded_at = data["responded_at"]
    if data.get("closed_at") is not None:
        enquiry.closed_at = data["closed_at"]
    if data.get("admin_notes") is not None:
        enquiry.admin_notes = data["admin_notes"]

    enquiry.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(enquiry)
    append_admin_activity(
        db,
        module="onboarding",
        change="Enquiry updated",
        details=f"Enquiry {enquiry.id} moved to {enquiry.status.value}",
        actor=actor,
        target_type="enquiry",
        target_id=str(enquiry.id),
    )
    return _serialize(enquiry)
