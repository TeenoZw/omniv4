"""add technician jobs table

Revision ID: b7c8d9e0f1a2
Revises: a1d2e3f4b5c6
Create Date: 2026-03-05 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = "a1d2e3f4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    technician_job_status = postgresql.ENUM(
        "pending",
        "assigned",
        "in_progress",
        "completed",
        "cancelled",
        name="technician_job_status",
        create_type=False,
    )
    technician_job_priority = postgresql.ENUM(
        "low",
        "normal",
        "high",
        "urgent",
        name="technician_job_priority",
        create_type=False,
    )
    technician_job_status.create(op.get_bind(), checkfirst=True)
    technician_job_priority.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "technician_jobs",
        sa.Column("hub_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("hardware_id", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("requested_by", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("assigned_technician_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("status", technician_job_status, nullable=False, server_default="pending"),
        sa.Column("priority", technician_job_priority, nullable=False, server_default="normal"),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("installed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("installation_location", sa.String(length=255), nullable=True),
        sa.Column("installation_latitude", sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column("installation_longitude", sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column("asset_label", sa.String(length=255), nullable=True),
        sa.Column("asset_registration", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("completion_notes", sa.Text(), nullable=True),
        sa.Column("assignment_reference", sa.String(length=64), nullable=True),
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assigned_technician_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["hardware_id"], ["hardware_inventory.id"]),
        sa.ForeignKeyConstraint(["hub_id"], ["hubs.id"]),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_technician_jobs_hub_id", "technician_jobs", ["hub_id"], unique=False)
    op.create_index("ix_technician_jobs_hardware_id", "technician_jobs", ["hardware_id"], unique=False)
    op.create_index("ix_technician_jobs_vehicle_id", "technician_jobs", ["vehicle_id"], unique=False)
    op.create_index("ix_technician_jobs_requested_by", "technician_jobs", ["requested_by"], unique=False)
    op.create_index(
        "ix_technician_jobs_assigned_technician_id",
        "technician_jobs",
        ["assigned_technician_id"],
        unique=False,
    )
    op.create_index("ix_technician_jobs_status", "technician_jobs", ["status"], unique=False)
    op.create_index("ix_technician_jobs_priority", "technician_jobs", ["priority"], unique=False)
    op.create_index("ix_technician_jobs_scheduled_for", "technician_jobs", ["scheduled_for"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_technician_jobs_scheduled_for", table_name="technician_jobs")
    op.drop_index("ix_technician_jobs_priority", table_name="technician_jobs")
    op.drop_index("ix_technician_jobs_status", table_name="technician_jobs")
    op.drop_index("ix_technician_jobs_assigned_technician_id", table_name="technician_jobs")
    op.drop_index("ix_technician_jobs_requested_by", table_name="technician_jobs")
    op.drop_index("ix_technician_jobs_vehicle_id", table_name="technician_jobs")
    op.drop_index("ix_technician_jobs_hardware_id", table_name="technician_jobs")
    op.drop_index("ix_technician_jobs_hub_id", table_name="technician_jobs")
    op.drop_table("technician_jobs")

    technician_job_priority = postgresql.ENUM(
        "low",
        "normal",
        "high",
        "urgent",
        name="technician_job_priority",
        create_type=False,
    )
    technician_job_status = postgresql.ENUM(
        "pending",
        "assigned",
        "in_progress",
        "completed",
        "cancelled",
        name="technician_job_status",
        create_type=False,
    )
    technician_job_priority.drop(op.get_bind(), checkfirst=True)
    technician_job_status.drop(op.get_bind(), checkfirst=True)
