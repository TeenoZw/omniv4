"""add optional vehicle columns

Revision ID: bcd1f978cd55
Revises: 3729276b4ab7
Create Date: 2025-12-09 13:24:41.400744

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bcd1f978cd55"
down_revision: Union[str, Sequence[str], None] = "3729276b4ab7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add optional vehicle metadata columns."""
    op.add_column("vehicles", sa.Column("vin", sa.String(length=64), nullable=True))
    op.add_column("vehicles", sa.Column("fuel_type", sa.String(length=50), nullable=True))
    op.add_column("vehicles", sa.Column("photo_url", sa.String(length=500), nullable=True))
    op.add_column("vehicles", sa.Column("notes", sa.String(length=500), nullable=True))
    op.create_index("ix_vehicles_vin", "vehicles", ["vin"], unique=True)


def downgrade() -> None:
    """Remove optional vehicle metadata columns."""
    op.drop_index("ix_vehicles_vin", table_name="vehicles")
    op.drop_column("vehicles", "notes")
    op.drop_column("vehicles", "photo_url")
    op.drop_column("vehicles", "fuel_type")
    op.drop_column("vehicles", "vin")
