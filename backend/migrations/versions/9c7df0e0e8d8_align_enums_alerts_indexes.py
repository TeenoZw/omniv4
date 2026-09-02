"""Align enums, add alerts table, and create missing indexes.

Revision ID: 9c7df0e0e8d8
Revises: 5a6f1d2d3c1b
Create Date: 2025-11-24 12:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "9c7df0e0e8d8"
down_revision = "5a6f1d2d3c1b"
branch_labels = None
depends_on = None


OLD_USER_ROLE = postgresql.ENUM(
    "ADMIN",
    "TECHNICIAN",
    "CLIENT",
    "COMPANY",
    name="userrole",
    create_type=False,
)
NEW_USER_ROLE = postgresql.ENUM(
    "admin",
    "technician",
    "client",
    "company",
    name="user_role",
)

OLD_VEHICLE_STATUS = postgresql.ENUM(
    "ACTIVE",
    "INACTIVE",
    "MAINTENANCE",
    "RETIRED",
    name="vehiclestatus",
    create_type=False,
)
NEW_VEHICLE_STATUS = postgresql.ENUM(
    "active",
    "inactive",
    "maintenance",
    "retired",
    name="vehicle_status",
)

OLD_DEVICE_STATUS = postgresql.ENUM(
    "ACTIVE",
    "INACTIVE",
    "FAULTY",
    "UNASSIGNED",
    name="devicestatus",
    create_type=False,
)
NEW_DEVICE_STATUS = postgresql.ENUM(
    "active",
    "inactive",
    "faulty",
    "unassigned",
    name="device_status",
)

OLD_SUBSCRIPTION_TIER = postgresql.ENUM(
    "FREE",
    "PRO",
    "ENTERPRISE",
    name="subscriptiontier",
    create_type=False,
)
NEW_SUBSCRIPTION_TIER = postgresql.ENUM(
    "free",
    "pro",
    "enterprise",
    name="subscription_tier",
)

ALERT_TYPE = postgresql.ENUM(
    "overspeed",
    "ignition",
    "geofence",
    "maintenance",
    "can_anomaly",
    "connection_loss",
    name="alert_type",
    create_type=False,
)
ALERT_SEVERITY = postgresql.ENUM(
    "info",
    "warning",
    "critical",
    name="alert_severity",
    create_type=False,
)


def _promote_enum(table: str, column: str, old_enum: postgresql.ENUM, new_enum: postgresql.ENUM, default: str | None) -> None:
    """Replace an uppercase enum with a lowercase version while preserving data."""

    bind = op.get_bind()
    new_enum.create(bind, checkfirst=True)
    op.alter_column(
        table,
        column,
        server_default=None,
        existing_type=old_enum,
        existing_nullable=False,
    )
    op.execute(
        sa.text(
            f"ALTER TABLE {table} ALTER COLUMN {column} "
            f"TYPE {new_enum.name} USING lower({column}::text):: {new_enum.name}"
        )
    )
    if default is not None:
        op.alter_column(
            table,
            column,
            server_default=sa.text(f"'{default}'"),
            existing_type=new_enum,
        )
    old_enum.drop(bind, checkfirst=True)


def upgrade() -> None:
    """Apply schema changes."""

    _promote_enum("users", "role", OLD_USER_ROLE, NEW_USER_ROLE, "client")
    _promote_enum("vehicles", "status", OLD_VEHICLE_STATUS, NEW_VEHICLE_STATUS, "active")
    _promote_enum("devices", "status", OLD_DEVICE_STATUS, NEW_DEVICE_STATUS, "unassigned")
    _promote_enum("subscriptions", "tier", OLD_SUBSCRIPTION_TIER, NEW_SUBSCRIPTION_TIER, "free")

    # Missing foreign-key indexes
    op.create_index("idx_hubs_owner_id", "hubs", ["owner_id"], unique=False)
    op.create_index("idx_vehicles_hub_id", "vehicles", ["hub_id"], unique=False)
    op.create_index("idx_devices_vehicle_id", "devices", ["vehicle_id"], unique=False)
    op.create_index("idx_devices_assigned_to", "devices", ["assigned_to"], unique=False)
    op.create_index("idx_subscriptions_user_id", "subscriptions", ["user_id"], unique=False)
    op.create_index("idx_subscriptions_is_active", "subscriptions", ["is_active"], unique=False)
    op.create_index("idx_technicians_user_id", "technicians", ["user_id"], unique=False)
    op.create_index("idx_technicians_hub_id", "technicians", ["hub_id"], unique=False)

    # Alerts table
    bind = op.get_bind()
    ALERT_TYPE.create(bind, checkfirst=True)
    ALERT_SEVERITY.create(bind, checkfirst=True)

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alert_type", ALERT_TYPE, nullable=False),
        sa.Column("severity", ALERT_SEVERITY, nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("is_acknowledged", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("triggered_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("idx_alerts_vehicle_time", "alerts", ["vehicle_id", "triggered_at"], unique=False)
    op.create_index("idx_alerts_severity", "alerts", ["severity"], unique=False)
    op.create_index("idx_alerts_ack", "alerts", ["is_acknowledged"], unique=False)


def downgrade() -> None:
    """Revert schema changes."""

    # Drop alert indexes/table/enums
    op.drop_index("idx_alerts_ack", table_name="alerts")
    op.drop_index("idx_alerts_severity", table_name="alerts")
    op.drop_index("idx_alerts_vehicle_time", table_name="alerts")
    op.drop_table("alerts")

    bind = op.get_bind()
    ALERT_SEVERITY.drop(bind, checkfirst=True)
    ALERT_TYPE.drop(bind, checkfirst=True)

    # Drop added indexes
    op.drop_index("idx_technicians_hub_id", table_name="technicians")
    op.drop_index("idx_technicians_user_id", table_name="technicians")
    op.drop_index("idx_subscriptions_is_active", table_name="subscriptions")
    op.drop_index("idx_subscriptions_user_id", table_name="subscriptions")
    op.drop_index("idx_devices_assigned_to", table_name="devices")
    op.drop_index("idx_devices_vehicle_id", table_name="devices")
    op.drop_index("idx_vehicles_hub_id", table_name="vehicles")
    op.drop_index("idx_hubs_owner_id", table_name="hubs")

    # Recreate original enums and convert values back to uppercase
    OLD_USER_ROLE.create(bind, checkfirst=True)
    op.execute(
        sa.text(
            "ALTER TABLE users ALTER COLUMN role TYPE userrole "
            "USING upper(role::text):: userrole"
        )
    )
    op.alter_column("users", "role", server_default=sa.text("'CLIENT'"))
    NEW_USER_ROLE.drop(bind, checkfirst=True)

    OLD_VEHICLE_STATUS.create(bind, checkfirst=True)
    op.execute(
        sa.text(
            "ALTER TABLE vehicles ALTER COLUMN status TYPE vehiclestatus "
            "USING upper(status::text):: vehiclestatus"
        )
    )
    op.alter_column("vehicles", "status", server_default=sa.text("'ACTIVE'"))
    NEW_VEHICLE_STATUS.drop(bind, checkfirst=True)

    OLD_DEVICE_STATUS.create(bind, checkfirst=True)
    op.execute(
        sa.text(
            "ALTER TABLE devices ALTER COLUMN status TYPE devicestatus "
            "USING upper(status::text):: devicestatus"
        )
    )
    op.alter_column("devices", "status", server_default=sa.text("'UNASSIGNED'"))
    NEW_DEVICE_STATUS.drop(bind, checkfirst=True)

    OLD_SUBSCRIPTION_TIER.create(bind, checkfirst=True)
    op.execute(
        sa.text(
            "ALTER TABLE subscriptions ALTER COLUMN tier TYPE subscriptiontier "
            "USING upper(tier::text):: subscriptiontier"
        )
    )
    op.alter_column("subscriptions", "tier", server_default=sa.text("'FREE'"))
    NEW_SUBSCRIPTION_TIER.drop(bind, checkfirst=True)
