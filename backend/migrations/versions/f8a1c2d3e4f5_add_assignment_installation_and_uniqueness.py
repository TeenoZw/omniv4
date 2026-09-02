"""add assignment installation metadata and active uniqueness guards

Revision ID: f8a1c2d3e4f5
Revises: c9d0e1f2a3b4
Create Date: 2026-02-27 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f8a1c2d3e4f5"
down_revision: Union[str, Sequence[str], None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("hardware_assignments", sa.Column("installed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("hardware_assignments", sa.Column("installation_location", sa.String(length=255), nullable=True))
    op.add_column("hardware_assignments", sa.Column("installation_latitude", sa.Numeric(precision=10, scale=7), nullable=True))
    op.add_column("hardware_assignments", sa.Column("installation_longitude", sa.Numeric(precision=10, scale=7), nullable=True))
    op.add_column("hardware_assignments", sa.Column("asset_label", sa.String(length=255), nullable=True))
    op.add_column("hardware_assignments", sa.Column("asset_registration", sa.String(length=100), nullable=True))

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_hw_assignment_active_hardware
        ON hardware_assignments (hardware_id)
        WHERE is_active = true;
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_hw_assignment_active_vehicle
        ON hardware_assignments (vehicle_id)
        WHERE is_active = true AND vehicle_id IS NOT NULL;
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_hw_assignment_active_asset_registration
        ON hardware_assignments (hub_id, asset_registration)
        WHERE is_active = true AND hub_id IS NOT NULL AND asset_registration IS NOT NULL;
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ux_hw_assignment_active_asset_registration")
    op.execute("DROP INDEX IF EXISTS ux_hw_assignment_active_vehicle")
    op.execute("DROP INDEX IF EXISTS ux_hw_assignment_active_hardware")

    op.drop_column("hardware_assignments", "asset_registration")
    op.drop_column("hardware_assignments", "asset_label")
    op.drop_column("hardware_assignments", "installation_longitude")
    op.drop_column("hardware_assignments", "installation_latitude")
    op.drop_column("hardware_assignments", "installation_location")
    op.drop_column("hardware_assignments", "installed_at")
