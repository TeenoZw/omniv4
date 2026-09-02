"""Drop legacy tracking tables (telemetry, trips, alerts)."""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "e3c4b5a6d7e8"
down_revision: Union[str, Sequence[str], None] = "d1f2c3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLES_TO_DROP = (
    "alerts",
    "telemetry",
    "telemetry_legacy",
    "telemetry_timescale",
    "trips",
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing = set(inspector.get_table_names())

    for table_name in TABLES_TO_DROP:
        if table_name in existing:
            op.drop_table(table_name)


def downgrade() -> None:
    # Legacy telemetry/trip/alert tables are intentionally removed in this pivot.
    pass
