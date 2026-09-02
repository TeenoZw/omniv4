"""add hardware inventory tables

Revision ID: 5a6f1d2d3c1b
Revises: 4ebfadd041b4
Create Date: 2025-11-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "5a6f1d2d3c1b"
down_revision: Union[str, Sequence[str], None] = "4ebfadd041b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

hardware_status = postgresql.ENUM(
    "in_stock",
    "assigned",
    "active",
    "faulty",
    "maintenance",
    "retired",
    name="hardwarestatus",
    create_type=False,
)


def upgrade() -> None:
    """Create hardware inventory tables."""
    bind = op.get_bind()
    hardware_status.create(bind, checkfirst=True)

    op.create_table(
        "hardware_inventory",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("imei", sa.String(length=32), nullable=False),
        sa.Column("serial_number", sa.String(length=64), nullable=True),
        sa.Column("hardware_type", sa.String(length=64), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("manufacturer", sa.String(length=100), nullable=True),
        sa.Column("firmware_version", sa.String(length=64), nullable=True),
        sa.Column("iccid", sa.String(length=32), nullable=True),
        sa.Column("purchase_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("purchase_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("status", hardware_status, nullable=False, server_default="in_stock"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("imei", name="uq_hardware_inventory_imei"),
        sa.UniqueConstraint("serial_number", name="uq_hardware_inventory_serial"),
        sa.UniqueConstraint("iccid", name="uq_hardware_inventory_iccid"),
    )
    op.create_index("ix_hardware_inventory_status", "hardware_inventory", ["status"])

    op.create_table(
        "hardware_assignments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("hardware_id", sa.Integer(), nullable=False),
        sa.Column("hub_id", sa.UUID(), nullable=True),
        sa.Column("vehicle_id", sa.UUID(), nullable=True),
        sa.Column("assigned_by", sa.UUID(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("unassigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["hardware_id"], ["hardware_inventory.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["hub_id"], ["hubs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "idx_hardware_assignments_active",
        "hardware_assignments",
        ["hardware_id", "is_active"],
    )


def downgrade() -> None:
    """Drop hardware inventory tables."""
    op.drop_index("idx_hardware_assignments_active", table_name="hardware_assignments")
    op.drop_table("hardware_assignments")
    op.drop_index("ix_hardware_inventory_status", table_name="hardware_inventory")
    op.drop_table("hardware_inventory")
    hardware_status.drop(op.get_bind(), checkfirst=True)
