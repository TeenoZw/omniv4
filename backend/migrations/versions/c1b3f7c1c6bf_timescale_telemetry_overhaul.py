"""Restructure telemetry table for Timescale hypertable.

Revision ID: c1b3f7c1c6bf
Revises: 9c7df0e0e8d8
Create Date: 2025-11-24 12:10:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c1b3f7c1c6bf"
down_revision = "9c7df0e0e8d8"
branch_labels = None
depends_on = None


def _ensure_hypertable(bind: sa.engine.Connection) -> None:
    """Create telemetry hypertable only when TimescaleDB is available."""

    has_extension = bind.execute(
        sa.text("SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'")
    ).first()
    if has_extension:
        bind.execute(
            sa.text("SELECT create_hypertable('telemetry', 'time', if_not_exists => TRUE);")
        )


def upgrade() -> None:
    """Replace the legacy telemetry table with an imei/time keyed hypertable."""

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # In the post-pivot branch, telemetry can already be dropped by a sibling migration.
    # Make this step idempotent across merge paths.
    if not inspector.has_table("telemetry"):
        return

    op.execute("ALTER TABLE IF EXISTS telemetry RENAME TO telemetry_legacy")
    inspector = sa.inspect(bind)
    if not inspector.has_table("telemetry_legacy"):
        return

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint c
                JOIN pg_class t ON c.conrelid = t.oid
                WHERE t.relname = 'telemetry_legacy' AND c.conname = 'telemetry_pkey'
            ) THEN
                ALTER TABLE telemetry_legacy RENAME CONSTRAINT telemetry_pkey TO telemetry_legacy_pkey;
            END IF;
        END $$;
        """
    )

    op.create_table(
        "telemetry",
        sa.Column("time", sa.DateTime(), nullable=False),
        sa.Column("imei", sa.String(length=20), nullable=False),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("speed_kmh", sa.Float(), nullable=True),
        sa.Column("heading", sa.Float(), nullable=True),
        sa.Column("ignition", sa.Boolean(), nullable=True),
        sa.Column("fuel_level", sa.Float(), nullable=True),
        sa.Column("rpm", sa.Integer(), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("odometer", sa.Float(), nullable=True),
        sa.Column("battery_voltage", sa.Float(), nullable=True),
        sa.Column("signal_strength", sa.Integer(), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["imei"], ["devices.imei"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("time", "imei", name="telemetry_pkey"),
    )

    # Populate the new table using existing telemetry + device associations
    op.execute(
        """
        INSERT INTO telemetry (
            time,
            imei,
            vehicle_id,
            trip_id,
            latitude,
            longitude,
            speed_kmh,
            heading,
            ignition,
            fuel_level,
            rpm,
            temperature,
            odometer,
            battery_voltage,
            signal_strength,
            raw_payload,
            created_at
        )
        SELECT
            tl.timestamp AS time,
            COALESCE(
                d.imei,
                'temp-' || RIGHT(regexp_replace(tl.id::text, '-', '', 'g'), 12)
            ) AS imei,
            tl.vehicle_id,
            tl.trip_id,
            tl.latitude,
            tl.longitude,
            tl.speed_kmh,
            tl.heading,
            tl.ignition,
            tl.fuel_level,
            tl.rpm,
            tl.temperature,
            tl.odometer,
            tl.battery_voltage,
            tl.signal_strength,
            CASE WHEN tl.raw_payload IS NULL THEN NULL ELSE to_jsonb(tl.raw_payload) END,
            tl.created_at
        FROM telemetry_legacy tl
        LEFT JOIN devices d ON tl.vehicle_id = d.vehicle_id
        """
    )

    op.drop_table("telemetry_legacy")

    op.create_index("idx_telemetry_imei_time", "telemetry", ["imei", "time"], unique=False)
    op.create_index("idx_telemetry_speed", "telemetry", ["speed_kmh"], unique=False)
    op.create_index("idx_telemetry_vehicle_time", "telemetry", ["vehicle_id", "time"], unique=False)
    op.create_index("idx_telemetry_trip_time", "telemetry", ["trip_id", "time"], unique=False)

    _ensure_hypertable(bind)


def downgrade() -> None:
    """Recreate the legacy telemetry table shape with UUID primary keys."""

    bind = op.get_bind()

    op.rename_table("telemetry", "telemetry_timescale")
    op.execute("ALTER TABLE telemetry_timescale RENAME CONSTRAINT telemetry_pkey TO telemetry_timescale_pkey")

    op.create_table(
        "telemetry",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("speed_kmh", sa.Float(), nullable=True),
        sa.Column("heading", sa.Float(), nullable=True),
        sa.Column("ignition", sa.Boolean(), nullable=True),
        sa.Column("fuel_level", sa.Float(), nullable=True),
        sa.Column("rpm", sa.Integer(), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("odometer", sa.Float(), nullable=True),
        sa.Column("battery_voltage", sa.Float(), nullable=True),
        sa.Column("signal_strength", sa.Integer(), nullable=True),
        sa.Column("raw_payload", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="telemetry_pkey"),
    )

    op.create_index("idx_telemetry_vehicle_timestamp", "telemetry", ["vehicle_id", "timestamp"], unique=False)
    op.create_index("idx_telemetry_trip_timestamp", "telemetry", ["trip_id", "timestamp"], unique=False)
    op.create_index("ix_telemetry_timestamp", "telemetry", ["timestamp"], unique=False)
    op.create_index("ix_telemetry_trip_id", "telemetry", ["trip_id"], unique=False)
    op.create_index("ix_telemetry_vehicle_id", "telemetry", ["vehicle_id"], unique=False)

    op.execute(
        """
        INSERT INTO telemetry (
            id,
            vehicle_id,
            trip_id,
            latitude,
            longitude,
            timestamp,
            speed_kmh,
            heading,
            ignition,
            fuel_level,
            rpm,
            temperature,
            odometer,
            battery_voltage,
            signal_strength,
            raw_payload,
            created_at,
            updated_at
        )
        SELECT
            (
                SUBSTR(hash, 1, 8) || '-' ||
                SUBSTR(hash, 9, 4) || '-' ||
                SUBSTR(hash, 13, 4) || '-' ||
                SUBSTR(hash, 17, 4) || '-' ||
                SUBSTR(hash, 21, 12)
            )::uuid AS id,
            src.vehicle_id,
            src.trip_id,
            src.latitude,
            src.longitude,
            src.time AS timestamp,
            src.speed_kmh,
            src.heading,
            src.ignition,
            src.fuel_level,
            src.rpm,
            src.temperature,
            src.odometer,
            src.battery_voltage,
            src.signal_strength,
            src.raw_payload_text,
            src.created_at,
            src.created_at AS updated_at
        FROM (
            SELECT
                COALESCE(tt.vehicle_id, d.vehicle_id) AS vehicle_id,
                tt.trip_id,
                tt.latitude,
                tt.longitude,
                tt.time,
                tt.speed_kmh,
                tt.heading,
                tt.ignition,
                tt.fuel_level,
                tt.rpm,
                tt.temperature,
                tt.odometer,
                tt.battery_voltage,
                tt.signal_strength,
                CASE
                    WHEN tt.raw_payload IS NULL THEN NULL
                    WHEN jsonb_typeof(tt.raw_payload) = 'string' THEN tt.raw_payload #>> '{}'
                    ELSE tt.raw_payload::text
                END AS raw_payload_text,
                tt.created_at,
                md5(tt.imei || tt.time::text) AS hash
            FROM telemetry_timescale tt
            LEFT JOIN devices d ON tt.imei = d.imei
            WHERE COALESCE(tt.vehicle_id, d.vehicle_id) IS NOT NULL
        ) AS src
        """
    )

    op.drop_table("telemetry_timescale")
