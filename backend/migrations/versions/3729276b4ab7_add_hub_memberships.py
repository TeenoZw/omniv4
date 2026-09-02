"""add hub memberships

Revision ID: 3729276b4ab7
Revises: 1dcf9cb39de7
Create Date: 2025-12-02 21:25:06.252671

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3729276b4ab7'
down_revision: Union[str, Sequence[str], None] = '1dcf9cb39de7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    hub_membership_status = postgresql.ENUM(
        "active",
        "invited",
        "suspended",
        name="hub_membership_status",
    )

    bind = op.get_bind()
    hub_membership_status.create(bind, checkfirst=True)
    hub_membership_status_type = postgresql.ENUM(
        "active",
        "invited",
        "suspended",
        name="hub_membership_status",
        create_type=False,
    )
    user_role_enum = postgresql.ENUM(
        "admin",
        "technician",
        "client",
        "company",
        name="user_role",
    )
    user_role_enum.create(bind, checkfirst=True)
    user_role_enum_type = postgresql.ENUM(
        "admin",
        "technician",
        "client",
        "company",
        name="user_role",
        create_type=False,
    )

    op.create_table(
        "hub_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("hub_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", user_role_enum_type, nullable=False),
        sa.Column("status", hub_membership_status_type, nullable=False, server_default=sa.text("'active'")),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["hub_id"], ["hubs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hub_id", "user_id", name="uq_hub_membership_user"),
    )

    op.create_index("ix_hub_memberships_hub_id", "hub_memberships", ["hub_id"], unique=False)
    op.create_index("ix_hub_memberships_user_id", "hub_memberships", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_hub_memberships_user_id", table_name="hub_memberships")
    op.drop_index("ix_hub_memberships_hub_id", table_name="hub_memberships")
    op.drop_table("hub_memberships")

    hub_membership_status = postgresql.ENUM(name="hub_membership_status")
    bind = op.get_bind()
    hub_membership_status.drop(bind, checkfirst=True)
