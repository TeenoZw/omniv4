"""add admin activity hash chain

Revision ID: a7b8c9d0e1f2
Revises: f4a5b6c7d8e9
Create Date: 2026-02-20 09:40:00.000000

"""
from __future__ import annotations

import hashlib
import json
from datetime import timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, None] = "f4a5b6c7d8e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _backfill_hash_chain() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            """
            SELECT
              id,
              created_at,
              module,
              change,
              details,
              actor_id,
              actor_name,
              actor_email,
              target_type,
              target_id
            FROM admin_activity_logs
            ORDER BY created_at ASC, id ASC
            """
        )
    ).mappings().all()

    previous_hash = None
    sequence_no = 1
    for row in rows:
        created_at = row["created_at"]
        if created_at is not None and getattr(created_at, "tzinfo", None) is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        payload = {
            "sequence_no": sequence_no,
            "created_at": created_at.isoformat() if created_at else None,
            "module": row["module"],
            "change": row["change"],
            "details": row["details"],
            "actor_id": str(row["actor_id"]) if row["actor_id"] else None,
            "actor_name": row["actor_name"],
            "actor_email": row["actor_email"],
            "target_type": row["target_type"],
            "target_id": row["target_id"],
            "previous_hash": previous_hash,
        }
        entry_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest()

        conn.execute(
            sa.text(
                """
                UPDATE admin_activity_logs
                SET sequence_no = :sequence_no,
                    previous_hash = :previous_hash,
                    entry_hash = :entry_hash
                WHERE id = :id
                """
            ),
            {
                "sequence_no": sequence_no,
                "previous_hash": previous_hash,
                "entry_hash": entry_hash,
                "id": row["id"],
            },
        )
        previous_hash = entry_hash
        sequence_no += 1


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "admin_activity_logs" not in inspector.get_table_names():
        op.create_table(
            "admin_activity_logs",
            sa.Column("module", sa.String(length=80), nullable=False),
            sa.Column("change", sa.String(length=255), nullable=False),
            sa.Column("details", sa.Text(), nullable=True),
            sa.Column("actor_id", sa.Uuid(), nullable=True),
            sa.Column("actor_name", sa.String(length=255), nullable=True),
            sa.Column("actor_email", sa.String(length=255), nullable=True),
            sa.Column("target_type", sa.String(length=80), nullable=True),
            sa.Column("target_id", sa.String(length=120), nullable=True),
            sa.Column("sequence_no", sa.Integer(), nullable=False),
            sa.Column("previous_hash", sa.String(length=64), nullable=True),
            sa.Column("entry_hash", sa.String(length=64), nullable=False),
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_admin_activity_logs_module"), "admin_activity_logs", ["module"], unique=False)
        op.create_index(op.f("ix_admin_activity_logs_actor_id"), "admin_activity_logs", ["actor_id"], unique=False)
        op.create_index(op.f("ix_admin_activity_logs_actor_email"), "admin_activity_logs", ["actor_email"], unique=False)
        op.create_index(op.f("ix_admin_activity_logs_target_type"), "admin_activity_logs", ["target_type"], unique=False)
        op.create_index(op.f("ix_admin_activity_logs_target_id"), "admin_activity_logs", ["target_id"], unique=False)
        op.create_index(op.f("ix_admin_activity_logs_sequence_no"), "admin_activity_logs", ["sequence_no"], unique=False)
        op.create_index(op.f("ix_admin_activity_logs_entry_hash"), "admin_activity_logs", ["entry_hash"], unique=True)
        return

    op.add_column("admin_activity_logs", sa.Column("sequence_no", sa.Integer(), nullable=True))
    op.add_column("admin_activity_logs", sa.Column("previous_hash", sa.String(length=64), nullable=True))
    op.add_column("admin_activity_logs", sa.Column("entry_hash", sa.String(length=64), nullable=True))

    _backfill_hash_chain()

    with op.batch_alter_table("admin_activity_logs") as batch_op:
        batch_op.alter_column("sequence_no", existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column("entry_hash", existing_type=sa.String(length=64), nullable=False)

    op.create_index(op.f("ix_admin_activity_logs_sequence_no"), "admin_activity_logs", ["sequence_no"], unique=False)
    op.create_index(op.f("ix_admin_activity_logs_entry_hash"), "admin_activity_logs", ["entry_hash"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_admin_activity_logs_entry_hash"), table_name="admin_activity_logs")
    op.drop_index(op.f("ix_admin_activity_logs_sequence_no"), table_name="admin_activity_logs")
    with op.batch_alter_table("admin_activity_logs") as batch_op:
        batch_op.drop_column("entry_hash")
        batch_op.drop_column("previous_hash")
        batch_op.drop_column("sequence_no")
