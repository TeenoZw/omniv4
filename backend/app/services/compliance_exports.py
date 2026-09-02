"""Helpers for compliance exports and evidence bundles."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
import csv
import json
from pathlib import Path
import zipfile

from app.core.config import settings
from app.models.compliance import ComplianceAttachment, DataSubjectRequest, SecurityIncident
from app.services.simple_pdf import build_simple_pdf


@dataclass
class AttachmentDescriptor:
    attachment: ComplianceAttachment
    file_path: Path


def compliance_storage_root() -> Path:
    root = Path(getattr(settings, "compliance_storage_dir", "") or "")
    if not root:
        root = Path(__file__).resolve().parents[3] / "storage" / "compliance_evidence"
    root.mkdir(parents=True, exist_ok=True)
    return root


def attachment_disk_path(attachment: ComplianceAttachment) -> Path:
    return compliance_storage_root() / attachment.stored_filename


def record_csv_bytes(headers: list[str], rows: list[list[object]]) -> bytes:
    buffer = BytesIO()
    text_stream = buffer
    import io
    wrapper = io.TextIOWrapper(text_stream, encoding="utf-8", newline="")
    writer = csv.writer(wrapper)
    writer.writerow(headers)
    writer.writerows(rows)
    wrapper.flush()
    return buffer.getvalue()


def _iso(value: datetime | None) -> str:
    return value.isoformat() if value else ""


def request_pdf_bytes(item: DataSubjectRequest, attachments: list[ComplianceAttachment]) -> bytes:
    sections = [
        ("Reference", [item.reference_no, f"Status: {item.status}", f"Type: {item.request_type}"]),
        (
            "Requester",
            [
                f"Requester: {item.requester_name}",
                f"Data subject: {item.data_subject_name or '—'}",
                f"Email: {item.requester_email or '—'}",
                f"Phone: {item.requester_phone or '—'}",
                f"Channel: {item.channel or '—'}",
                f"Identity verified: {'Yes' if item.identity_verified else 'No'}",
            ],
        ),
        (
            "Handling",
            [
                f"Assigned owner: {item.assigned_owner or '—'}",
                f"Due date: {_iso(item.due_date) or '—'}",
                f"Responded at: {_iso(item.responded_at) or '—'}",
                f"Closed at: {_iso(item.closed_at) or '—'}",
                f"Legal basis: {item.legal_basis or '—'}",
            ],
        ),
        ("Summary", [item.summary or "—"]),
        ("Decision", [item.decision or "—"]),
        ("Notes", [item.notes or "—"]),
        (
            "Evidence files",
            [
                f"{attachment.title or attachment.original_filename} ({attachment.original_filename}, {attachment.size_bytes} bytes)"
                for attachment in attachments
            ]
            or ["No evidence files attached"],
        ),
    ]
    return build_simple_pdf(f"Data Subject Request {item.reference_no}", sections)


def incident_pdf_bytes(item: SecurityIncident, attachments: list[ComplianceAttachment]) -> bytes:
    sections = [
        (
            "Reference",
            [
                item.reference_no,
                f"Status: {item.status}",
                f"Type: {item.incident_type}",
                f"Severity: {item.severity}",
            ],
        ),
        (
            "Incident context",
            [
                f"Reported by: {item.reported_by or '—'}",
                f"Owner: {item.owner or '—'}",
                f"Detected at: {_iso(item.detected_at) or '—'}",
                f"Closed at: {_iso(item.closed_at) or '—'}",
                f"Information Officer notified: {'Yes' if item.information_officer_notified else 'No'}",
                f"Regulator notification required: {'Yes' if item.regulator_notification_required else 'No'}",
                f"Data subject notification required: {'Yes' if item.data_subject_notification_required else 'No'}",
            ],
        ),
        ("Summary", [item.summary or "—"]),
        ("Systems affected", [item.systems_affected or "—"]),
        ("Information affected", [item.information_affected or "—"]),
        ("Containment", [item.containment_action or "—"]),
        ("Impact assessment", [item.impact_assessment or "—"]),
        ("Lessons learned", [item.lessons_learned or "—"]),
        ("Notes", [item.notes or "—"]),
        (
            "Evidence files",
            [
                f"{attachment.title or attachment.original_filename} ({attachment.original_filename}, {attachment.size_bytes} bytes)"
                for attachment in attachments
            ]
            or ["No evidence files attached"],
        ),
    ]
    return build_simple_pdf(f"Security Incident {item.reference_no}", sections)


def request_export_pack(item: DataSubjectRequest, attachments: list[ComplianceAttachment]) -> bytes:
    return _build_pack(
        base_name=item.reference_no.lower(),
        summary={
            "reference_no": item.reference_no,
            "request_type": item.request_type,
            "status": item.status,
            "requester_name": item.requester_name,
            "data_subject_name": item.data_subject_name,
            "requester_email": item.requester_email,
            "requester_phone": item.requester_phone,
            "channel": item.channel,
            "identity_verified": item.identity_verified,
            "summary": item.summary,
            "assigned_owner": item.assigned_owner,
            "due_date": _iso(item.due_date),
            "decision": item.decision,
            "responded_at": _iso(item.responded_at),
            "closed_at": _iso(item.closed_at),
            "legal_basis": item.legal_basis,
            "notes": item.notes,
            "created_at": _iso(item.created_at),
            "updated_at": _iso(item.updated_at),
        },
        attachment_rows=[
            [
                attachment.id,
                attachment.title or "",
                attachment.original_filename,
                attachment.mime_type or "",
                attachment.size_bytes,
                attachment.uploaded_by or "",
                _iso(attachment.created_at),
            ]
            for attachment in attachments
        ],
        pdf_bytes=request_pdf_bytes(item, attachments),
        attachments=attachments,
    )


def incident_export_pack(item: SecurityIncident, attachments: list[ComplianceAttachment]) -> bytes:
    return _build_pack(
        base_name=item.reference_no.lower(),
        summary={
            "reference_no": item.reference_no,
            "incident_type": item.incident_type,
            "status": item.status,
            "severity": item.severity,
            "reported_by": item.reported_by,
            "systems_affected": item.systems_affected,
            "information_affected": item.information_affected,
            "summary": item.summary,
            "containment_action": item.containment_action,
            "impact_assessment": item.impact_assessment,
            "owner": item.owner,
            "information_officer_notified": item.information_officer_notified,
            "regulator_notification_required": item.regulator_notification_required,
            "data_subject_notification_required": item.data_subject_notification_required,
            "regulator_notified_at": _iso(item.regulator_notified_at),
            "data_subjects_notified_at": _iso(item.data_subjects_notified_at),
            "detected_at": _iso(item.detected_at),
            "closed_at": _iso(item.closed_at),
            "lessons_learned": item.lessons_learned,
            "notes": item.notes,
            "created_at": _iso(item.created_at),
            "updated_at": _iso(item.updated_at),
        },
        attachment_rows=[
            [
                attachment.id,
                attachment.title or "",
                attachment.original_filename,
                attachment.mime_type or "",
                attachment.size_bytes,
                attachment.uploaded_by or "",
                _iso(attachment.created_at),
            ]
            for attachment in attachments
        ],
        pdf_bytes=incident_pdf_bytes(item, attachments),
        attachments=attachments,
    )


def _build_pack(
    *,
    base_name: str,
    summary: dict,
    attachment_rows: list[list[object]],
    pdf_bytes: bytes,
    attachments: list[ComplianceAttachment],
) -> bytes:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pack = BytesIO()
    with zipfile.ZipFile(pack, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("summary.json", json.dumps(summary, indent=2, default=str))
        bundle.writestr(
            "evidence_index.csv",
            record_csv_bytes(
                ["id", "title", "original_filename", "mime_type", "size_bytes", "uploaded_by", "created_at"],
                attachment_rows,
            ),
        )
        bundle.writestr(f"{base_name}_summary.pdf", pdf_bytes)
        for attachment in attachments:
            file_path = attachment_disk_path(attachment)
            if file_path.exists():
                bundle.write(file_path, arcname=f"attachments/{attachment.original_filename}")
    pack.seek(0)
    return pack.getvalue()
