"""add currency and billing contact phone to hubs

Revision ID: f0c9d2e3c4a1
Revises: e9a2f1c5d2ab
Create Date: 2025-12-11 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f0c9d2e3c4a1"
down_revision: Union[str, Sequence[str], None] = "e9a2f1c5d2ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("hubs", sa.Column("currency", sa.String(length=10), nullable=True))
    op.add_column("hubs", sa.Column("billing_contact_phone", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("hubs", "billing_contact_phone")
    op.drop_column("hubs", "currency")
