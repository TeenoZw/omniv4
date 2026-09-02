"""add hub recycle bin columns

Revision ID: a1d2e3f4b5c6
Revises: f8a1c2d3e4f5
Create Date: 2026-03-03 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1d2e3f4b5c6"
down_revision: Union[str, Sequence[str], None] = "f8a1c2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("hubs", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("hubs", sa.Column("recycle_bin_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_hubs_deleted_at", "hubs", ["deleted_at"], unique=False)
    op.create_index("ix_hubs_recycle_bin_expires_at", "hubs", ["recycle_bin_expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_hubs_recycle_bin_expires_at", table_name="hubs")
    op.drop_index("ix_hubs_deleted_at", table_name="hubs")
    op.drop_column("hubs", "recycle_bin_expires_at")
    op.drop_column("hubs", "deleted_at")
