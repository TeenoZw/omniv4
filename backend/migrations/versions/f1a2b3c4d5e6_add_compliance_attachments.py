"""Add compliance attachments table.

Revision ID: f1a2b3c4d5e6
Revises: e6f7a8b9c0d1
Create Date: 2026-04-06 12:45:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "f1a2b3c4d5e6"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def ensure_index(table_name: str, index_name: str, *columns: str, unique: bool = False) -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    indexes = {index["name"] for index in inspector.get_indexes(table_name)}
    if index_name not in indexes:
        op.create_index(index_name, table_name, list(columns), unique=unique)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "compliance_attachments" not in tables:
        op.create_table(
            "compliance_attachments",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("data_subject_request_id", sa.Integer(), nullable=True),
            sa.Column("security_incident_id", sa.Integer(), nullable=True),
            sa.Column("title", sa.String(length=255), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("original_filename", sa.String(length=255), nullable=False),
            sa.Column("stored_filename", sa.String(length=255), nullable=False),
            sa.Column("mime_type", sa.String(length=255), nullable=True),
            sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("uploaded_by", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["data_subject_request_id"], ["data_subject_requests.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["security_incident_id"], ["security_incidents.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    ensure_index("compliance_attachments", "ix_compliance_attachments_data_subject_request_id", "data_subject_request_id")
    ensure_index("compliance_attachments", "ix_compliance_attachments_security_incident_id", "security_incident_id")
    ensure_index("compliance_attachments", "ix_compliance_attachments_stored_filename", "stored_filename", unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if "compliance_attachments" in tables:
        op.drop_table("compliance_attachments")
