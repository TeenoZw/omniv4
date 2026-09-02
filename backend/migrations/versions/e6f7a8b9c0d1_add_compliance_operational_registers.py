"""add compliance operational registers

Revision ID: e6f7a8b9c0d1
Revises: d4e5f6a7b8c9, f8a1c2d3e4f5
Create Date: 2026-04-06 14:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "e6f7a8b9c0d1"
down_revision: Union[str, Sequence[str], None] = ("d4e5f6a7b8c9", "f8a1c2d3e4f5")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    def ensure_index(table_name: str, index_name: str, columns: list[str]) -> None:
        existing_indexes = {index["name"] for index in inspector.get_indexes(table_name)}
        if index_name not in existing_indexes:
            op.create_index(index_name, table_name, columns, unique=False)

    if "data_subject_requests" not in existing_tables:
        op.create_table(
            "data_subject_requests",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("reference_no", sa.String(length=32), nullable=False),
            sa.Column("request_type", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=64), server_default="new", nullable=False),
            sa.Column("requester_name", sa.String(length=255), nullable=False),
            sa.Column("data_subject_name", sa.String(length=255), nullable=True),
            sa.Column("requester_email", sa.String(length=255), nullable=True),
            sa.Column("requester_phone", sa.String(length=64), nullable=True),
            sa.Column("channel", sa.String(length=64), nullable=True),
            sa.Column("identity_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column("assigned_owner", sa.String(length=255), nullable=True),
            sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("decision", sa.Text(), nullable=True),
            sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("legal_basis", sa.String(length=255), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("reference_no"),
        )
        existing_tables.add("data_subject_requests")

    ensure_index("data_subject_requests", op.f("ix_data_subject_requests_reference_no"), ["reference_no"])
    ensure_index("data_subject_requests", op.f("ix_data_subject_requests_request_type"), ["request_type"])
    ensure_index("data_subject_requests", op.f("ix_data_subject_requests_status"), ["status"])
    ensure_index("data_subject_requests", op.f("ix_data_subject_requests_requester_email"), ["requester_email"])
    ensure_index("data_subject_requests", op.f("ix_data_subject_requests_assigned_owner"), ["assigned_owner"])
    ensure_index("data_subject_requests", op.f("ix_data_subject_requests_due_date"), ["due_date"])

    if "security_incidents" not in existing_tables:
        op.create_table(
            "security_incidents",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("reference_no", sa.String(length=32), nullable=False),
            sa.Column("incident_type", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=64), server_default="open", nullable=False),
            sa.Column("severity", sa.String(length=32), server_default="medium", nullable=False),
            sa.Column("reported_by", sa.String(length=255), nullable=True),
            sa.Column("systems_affected", sa.Text(), nullable=True),
            sa.Column("information_affected", sa.Text(), nullable=True),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column("containment_action", sa.Text(), nullable=True),
            sa.Column("impact_assessment", sa.Text(), nullable=True),
            sa.Column("owner", sa.String(length=255), nullable=True),
            sa.Column("information_officer_notified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("regulator_notification_required", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("data_subject_notification_required", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("regulator_notified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("data_subjects_notified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("detected_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("lessons_learned", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("reference_no"),
        )

    ensure_index("security_incidents", op.f("ix_security_incidents_reference_no"), ["reference_no"])
    ensure_index("security_incidents", op.f("ix_security_incidents_incident_type"), ["incident_type"])
    ensure_index("security_incidents", op.f("ix_security_incidents_status"), ["status"])
    ensure_index("security_incidents", op.f("ix_security_incidents_severity"), ["severity"])
    ensure_index("security_incidents", op.f("ix_security_incidents_owner"), ["owner"])
    ensure_index("security_incidents", op.f("ix_security_incidents_detected_at"), ["detected_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_security_incidents_detected_at"), table_name="security_incidents")
    op.drop_index(op.f("ix_security_incidents_owner"), table_name="security_incidents")
    op.drop_index(op.f("ix_security_incidents_severity"), table_name="security_incidents")
    op.drop_index(op.f("ix_security_incidents_status"), table_name="security_incidents")
    op.drop_index(op.f("ix_security_incidents_incident_type"), table_name="security_incidents")
    op.drop_index(op.f("ix_security_incidents_reference_no"), table_name="security_incidents")
    op.drop_table("security_incidents")

    op.drop_index(op.f("ix_data_subject_requests_due_date"), table_name="data_subject_requests")
    op.drop_index(op.f("ix_data_subject_requests_assigned_owner"), table_name="data_subject_requests")
    op.drop_index(op.f("ix_data_subject_requests_requester_email"), table_name="data_subject_requests")
    op.drop_index(op.f("ix_data_subject_requests_status"), table_name="data_subject_requests")
    op.drop_index(op.f("ix_data_subject_requests_request_type"), table_name="data_subject_requests")
    op.drop_index(op.f("ix_data_subject_requests_reference_no"), table_name="data_subject_requests")
    op.drop_table("data_subject_requests")
