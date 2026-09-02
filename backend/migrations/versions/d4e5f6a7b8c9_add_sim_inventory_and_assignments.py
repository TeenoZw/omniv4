"""add sim inventory and assignments

Revision ID: d4e5f6a7b8c9
Revises: c2d4e6f8a1b0
Create Date: 2026-03-29 12:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c2d4e6f8a1b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


simstatus = postgresql.ENUM(
    "in_stock",
    "assigned",
    "suspended",
    "faulty",
    "retired",
    name="simstatus",
    create_type=False,
)


def upgrade() -> None:
    simstatus.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "sim_inventory",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("iccid", sa.String(length=32), nullable=False),
        sa.Column("msisdn", sa.String(length=32), nullable=True),
        sa.Column("carrier", sa.String(length=100), server_default="Econet", nullable=False),
        sa.Column("apn", sa.String(length=128), nullable=True),
        sa.Column("roaming_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("roaming_regions", sa.Text(), nullable=True),
        sa.Column("status", simstatus, nullable=False, server_default="in_stock"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("iccid"),
        sa.UniqueConstraint("msisdn"),
    )
    op.create_index(op.f("ix_sim_inventory_iccid"), "sim_inventory", ["iccid"], unique=False)
    op.create_index(op.f("ix_sim_inventory_msisdn"), "sim_inventory", ["msisdn"], unique=False)
    op.create_index(op.f("ix_sim_inventory_status"), "sim_inventory", ["status"], unique=False)

    op.create_table(
        "sim_assignments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sim_id", sa.Integer(), nullable=False),
        sa.Column("hardware_id", sa.Integer(), nullable=False),
        sa.Column("hub_id", sa.Uuid(), nullable=True),
        sa.Column("vehicle_id", sa.Uuid(), nullable=True),
        sa.Column("assigned_by", sa.Uuid(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("unassigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["hardware_id"], ["hardware_inventory.id"]),
        sa.ForeignKeyConstraint(["hub_id"], ["hubs.id"]),
        sa.ForeignKeyConstraint(["sim_id"], ["sim_inventory.id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sim_assignments_hardware_id"), "sim_assignments", ["hardware_id"], unique=False)
    op.create_index(op.f("ix_sim_assignments_sim_id"), "sim_assignments", ["sim_id"], unique=False)
    op.create_index("ix_sim_assignments_active_per_sim", "sim_assignments", ["sim_id", "is_active"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_sim_assignments_active_per_sim", table_name="sim_assignments")
    op.drop_index(op.f("ix_sim_assignments_sim_id"), table_name="sim_assignments")
    op.drop_index(op.f("ix_sim_assignments_hardware_id"), table_name="sim_assignments")
    op.drop_table("sim_assignments")

    op.drop_index(op.f("ix_sim_inventory_status"), table_name="sim_inventory")
    op.drop_index(op.f("ix_sim_inventory_msisdn"), table_name="sim_inventory")
    op.drop_index(op.f("ix_sim_inventory_iccid"), table_name="sim_inventory")
    op.drop_table("sim_inventory")

    simstatus.drop(op.get_bind(), checkfirst=True)
