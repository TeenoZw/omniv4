"""add device pairings table

Revision ID: 4c42974c8dc0
Revises: 5a6f1d2d3c1b
Create Date: 2025-12-09 12:28:36.966011

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "4c42974c8dc0"
down_revision: Union[str, Sequence[str], None] = "5a6f1d2d3c1b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

pairing_status = postgresql.ENUM(
    "pending",
    "approved",
    "rejected",
    name="pairing_status",
    create_type=False,
)


def upgrade() -> None:
    """Add device_pairings table and enum."""
    bind = op.get_bind()
    pairing_status.create(bind, checkfirst=True)

    op.create_table(
        "device_pairings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("hardware_id", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.UUID(), nullable=False),
        sa.Column("requested_by", sa.UUID(), nullable=True),
        sa.Column("approved_by", sa.UUID(), nullable=True),
        sa.Column(
            "status",
            pairing_status,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["hardware_id"], ["hardware_inventory.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_device_pairings_status", "device_pairings", ["status"])


def downgrade() -> None:
    """Drop device_pairings artifacts."""
    op.drop_index("ix_device_pairings_status", table_name="device_pairings")
    op.drop_table("device_pairings")
    pairing_status.drop(op.get_bind(), checkfirst=True)
