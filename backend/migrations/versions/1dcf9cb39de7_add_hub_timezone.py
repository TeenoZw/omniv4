"""add hub timezone

Revision ID: 1dcf9cb39de7
Revises: 9beb80e7756c
Create Date: 2025-12-02 21:23:54.527981

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1dcf9cb39de7'
down_revision: Union[str, Sequence[str], None] = '9beb80e7756c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("hubs", sa.Column("timezone", sa.String(length=64), nullable=True))

    # Provide a sensible default for existing rows
    op.execute("UPDATE hubs SET timezone = 'Africa/Harare' WHERE timezone IS NULL")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("hubs", "timezone")
