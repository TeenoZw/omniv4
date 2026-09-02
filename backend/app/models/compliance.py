"""Operational compliance register models."""
from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.models import Base


class DataSubjectRequest(Base):
    """Tracks operational handling of data subject requests."""

    __tablename__ = "data_subject_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reference_no = Column(String(32), unique=True, nullable=False, index=True)
    request_type = Column(String(64), nullable=False, index=True)
    status = Column(String(64), nullable=False, index=True, server_default="new")
    requester_name = Column(String(255), nullable=False)
    data_subject_name = Column(String(255), nullable=True)
    requester_email = Column(String(255), nullable=True, index=True)
    requester_phone = Column(String(64), nullable=True)
    channel = Column(String(64), nullable=True)
    identity_verified = Column(Boolean, nullable=False, default=False, server_default="false")
    summary = Column(Text, nullable=False)
    assigned_owner = Column(String(255), nullable=True, index=True)
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    decision = Column(Text, nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    legal_basis = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    attachments = relationship(
        "ComplianceAttachment",
        back_populates="request",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ComplianceAttachment.created_at.desc()",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<DataSubjectRequest ref={self.reference_no} status={self.status}>"


class SecurityIncident(Base):
    """Tracks operational security incidents and regulator-facing evidence."""

    __tablename__ = "security_incidents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reference_no = Column(String(32), unique=True, nullable=False, index=True)
    incident_type = Column(String(64), nullable=False, index=True)
    status = Column(String(64), nullable=False, index=True, server_default="open")
    severity = Column(String(32), nullable=False, index=True, server_default="medium")
    reported_by = Column(String(255), nullable=True)
    systems_affected = Column(Text, nullable=True)
    information_affected = Column(Text, nullable=True)
    summary = Column(Text, nullable=False)
    containment_action = Column(Text, nullable=True)
    impact_assessment = Column(Text, nullable=True)
    owner = Column(String(255), nullable=True, index=True)
    information_officer_notified = Column(Boolean, nullable=False, default=False, server_default="false")
    regulator_notification_required = Column(Boolean, nullable=False, default=False, server_default="false")
    data_subject_notification_required = Column(Boolean, nullable=False, default=False, server_default="false")
    regulator_notified_at = Column(DateTime(timezone=True), nullable=True)
    data_subjects_notified_at = Column(DateTime(timezone=True), nullable=True)
    detected_at = Column(DateTime(timezone=True), nullable=True, index=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    lessons_learned = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    attachments = relationship(
        "ComplianceAttachment",
        back_populates="incident",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ComplianceAttachment.created_at.desc()",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<SecurityIncident ref={self.reference_no} status={self.status}>"


class ComplianceAttachment(Base):
    """Stores evidence files linked to compliance register records."""

    __tablename__ = "compliance_attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data_subject_request_id = Column(
        Integer,
        ForeignKey("data_subject_requests.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    security_incident_id = Column(
        Integer,
        ForeignKey("security_incidents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False, unique=True, index=True)
    mime_type = Column(String(255), nullable=True)
    size_bytes = Column(Integer, nullable=False, default=0)
    uploaded_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    request = relationship("DataSubjectRequest", back_populates="attachments")
    incident = relationship("SecurityIncident", back_populates="attachments")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<ComplianceAttachment file={self.original_filename} id={self.id}>"
