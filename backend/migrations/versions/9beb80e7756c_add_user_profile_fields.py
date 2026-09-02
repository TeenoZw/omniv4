"""add user profile fields

Revision ID: 9beb80e7756c
Revises: 1d0f3e8a6c1b
Create Date: 2025-12-02 21:21:59.367347

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9beb80e7756c'
down_revision: Union[str, Sequence[str], None] = '1d0f3e8a6c1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("first_name", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(length=255), nullable=True))
    # Backfill first_name using existing name data for better defaults
    op.execute("UPDATE users SET first_name = name WHERE first_name IS NULL")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
