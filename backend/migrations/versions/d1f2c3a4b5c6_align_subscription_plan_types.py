"""Align subscription plan types with Individual/Business."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d1f2c3a4b5c6"
down_revision = "f0c9d2e3c4a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("subscriptions", sa.Column("hub_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_subscriptions_hub_id",
        "subscriptions",
        "hubs",
        ["hub_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # Convert enum -> text first to avoid invalid enum writes during remapping.
    op.execute("ALTER TABLE subscriptions ALTER COLUMN tier TYPE VARCHAR(50) USING lower(tier::text)")
    op.execute(
        "UPDATE subscriptions SET tier = 'individual' WHERE tier IN ('free', 'basic')"
    )
    op.execute(
        "UPDATE subscriptions SET tier = 'business' WHERE tier IN ('pro', 'enterprise')"
    )
    op.execute("ALTER TABLE subscriptions ALTER COLUMN tier SET DEFAULT 'individual'")


def downgrade() -> None:
    op.drop_constraint("fk_subscriptions_hub_id", "subscriptions", type_="foreignkey")
    op.drop_column("subscriptions", "hub_id")
    op.alter_column(
        "subscriptions",
        "tier",
        existing_type=sa.String(length=50),
        type_=sa.Enum(name="subscription_tier"),
        nullable=False,
    )
