"""add enquiry profile fields

Revision ID: 7f1a7d9c5b1a
Revises: 2f4b8e9a1c7d
Create Date: 2026-02-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "7f1a7d9c5b1a"
down_revision: Union[str, Sequence[str], None] = "2f4b8e9a1c7d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add enquiry profile fields."""
    op.add_column("enquiries", sa.Column("fleet_size", sa.String(length=40), nullable=True))
    op.add_column("enquiries", sa.Column("operating_area", sa.String(length=255), nullable=True))
    op.add_column("enquiries", sa.Column("preferred_contact_method", sa.String(length=40), nullable=True))
    op.add_column("enquiries", sa.Column("expected_go_live_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("enquiries", sa.Column("tracking_use_case", sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Drop enquiry profile fields."""
    op.drop_column("enquiries", "tracking_use_case")
    op.drop_column("enquiries", "expected_go_live_date")
    op.drop_column("enquiries", "preferred_contact_method")
    op.drop_column("enquiries", "operating_area")
    op.drop_column("enquiries", "fleet_size")
