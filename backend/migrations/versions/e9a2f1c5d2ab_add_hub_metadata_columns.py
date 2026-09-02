"""add hub metadata columns

Revision ID: e9a2f1c5d2ab
Revises: 1dcf9cb39de7
Create Date: 2025-12-10 12:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e9a2f1c5d2ab"
down_revision: Union[str, Sequence[str], None] = "1dcf9cb39de7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("hubs", sa.Column("hub_type", sa.String(length=50), nullable=True))
    op.add_column("hubs", sa.Column("subscription_tier", sa.String(length=50), nullable=True))
    op.add_column("hubs", sa.Column("payment_method", sa.String(length=50), nullable=True))
    op.add_column("hubs", sa.Column("billing_cycle", sa.String(length=50), nullable=True))
    op.add_column("hubs", sa.Column("status", sa.String(length=50), nullable=True))
    op.add_column("hubs", sa.Column("country", sa.String(length=120), nullable=True))
    op.add_column("hubs", sa.Column("city", sa.String(length=120), nullable=True))
    op.add_column("hubs", sa.Column("address_line", sa.String(length=255), nullable=True))
    op.add_column("hubs", sa.Column("go_live_date", sa.Date(), nullable=True))
    op.add_column("hubs", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column("hubs", sa.Column("primary_contact_name", sa.String(length=255), nullable=True))
    op.add_column("hubs", sa.Column("primary_contact_email", sa.String(length=255), nullable=True))
    op.add_column("hubs", sa.Column("primary_contact_phone", sa.String(length=50), nullable=True))
    op.add_column("hubs", sa.Column("billing_contact_name", sa.String(length=255), nullable=True))
    op.add_column("hubs", sa.Column("billing_contact_email", sa.String(length=255), nullable=True))
    op.add_column("hubs", sa.Column("device_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("hubs", sa.Column("vehicle_count", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("hubs", "vehicle_count")
    op.drop_column("hubs", "device_count")
    op.drop_column("hubs", "billing_contact_email")
    op.drop_column("hubs", "billing_contact_name")
    op.drop_column("hubs", "primary_contact_phone")
    op.drop_column("hubs", "primary_contact_email")
    op.drop_column("hubs", "primary_contact_name")
    op.drop_column("hubs", "notes")
    op.drop_column("hubs", "go_live_date")
    op.drop_column("hubs", "address_line")
    op.drop_column("hubs", "city")
    op.drop_column("hubs", "country")
    op.drop_column("hubs", "status")
    op.drop_column("hubs", "billing_cycle")
    op.drop_column("hubs", "payment_method")
    op.drop_column("hubs", "subscription_tier")
    op.drop_column("hubs", "hub_type")

