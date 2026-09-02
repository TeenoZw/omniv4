"""rework assets and job cards for onboarding workflow

Revision ID: c2d4e6f8a1b0
Revises: b7c8d9e0f1a2
Create Date: 2026-03-25 18:15:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c2d4e6f8a1b0"
down_revision: Union[str, Sequence[str], None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("technician_jobs", "hardware_id", existing_type=sa.Integer(), nullable=True)
    op.add_column("technician_jobs", sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("technician_jobs", sa.Column("declined_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("technician_jobs", sa.Column("decline_reason", sa.Text(), nullable=True))

    op.alter_column("vehicles", "imei", existing_type=sa.String(length=20), nullable=True)
    op.alter_column("vehicles", "license_plate", existing_type=sa.String(length=20), nullable=True)
    op.add_column("vehicles", sa.Column("asset_type", sa.String(length=50), server_default="vehicle", nullable=False))
    op.add_column("vehicles", sa.Column("asset_name", sa.String(length=255), server_default="Unnamed asset", nullable=False))
    op.add_column("vehicles", sa.Column("asset_type_other", sa.String(length=100), nullable=True))
    op.add_column("vehicles", sa.Column("color", sa.String(length=50), nullable=True))
    op.add_column("vehicles", sa.Column("engine_capacity", sa.String(length=50), nullable=True))
    op.add_column("vehicles", sa.Column("co2_emissions", sa.String(length=50), nullable=True))
    op.add_column("vehicles", sa.Column("source_job_id", sa.Uuid(), nullable=True))
    op.create_index(op.f("ix_vehicles_source_job_id"), "vehicles", ["source_job_id"], unique=False)
    op.create_foreign_key(
        "fk_vehicles_source_job_id_technician_jobs",
        "vehicles",
        "technician_jobs",
        ["source_job_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_vehicles_source_job_id_technician_jobs", "vehicles", type_="foreignkey")
    op.drop_index(op.f("ix_vehicles_source_job_id"), table_name="vehicles")
    op.drop_column("vehicles", "source_job_id")
    op.drop_column("vehicles", "co2_emissions")
    op.drop_column("vehicles", "engine_capacity")
    op.drop_column("vehicles", "color")
    op.drop_column("vehicles", "asset_type_other")
    op.drop_column("vehicles", "asset_name")
    op.drop_column("vehicles", "asset_type")
    op.alter_column("vehicles", "license_plate", existing_type=sa.String(length=20), nullable=False)
    op.alter_column("vehicles", "imei", existing_type=sa.String(length=20), nullable=False)

    op.drop_column("technician_jobs", "decline_reason")
    op.drop_column("technician_jobs", "declined_at")
    op.drop_column("technician_jobs", "accepted_at")
    op.alter_column("technician_jobs", "hardware_id", existing_type=sa.Integer(), nullable=False)
