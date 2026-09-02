"""merge all heads for post-pivot baseline

Revision ID: c9d0e1f2a3b4
Revises: 4c42974c8dc0, 7f1a7d9c5b1a, a7b8c9d0e1f2, bcd1f978cd55
Create Date: 2026-02-23 23:30:00.000000

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = (
    "4c42974c8dc0",
    "7f1a7d9c5b1a",
    "a7b8c9d0e1f2",
    "bcd1f978cd55",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
