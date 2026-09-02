"""enforce unique hub codes

Revision ID: 1d0f3e8a6c1b
Revises: 4ebfadd041b4
Create Date: 2025-11-27 09:45:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import secrets
import string

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1d0f3e8a6c1b"
down_revision: Union[str, Sequence[str], None] = "4ebfadd041b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ALPHABET = string.ascii_uppercase + string.digits
PREFIX = "HUB-"
CODE_LENGTH = 8


def _generate_code() -> str:
    token = "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))
    return f"{PREFIX}{token}"


def _assign_missing_codes(connection, hubs_table):
    rows = connection.execute(sa.select(hubs_table.c.id, hubs_table.c.code)).fetchall()
    existing_codes = {row.code for row in rows if row.code}

    for row in rows:
        if row.code:
            continue

        code = _next_unique_code(connection, hubs_table, existing_codes)
        connection.execute(
            sa.update(hubs_table).where(hubs_table.c.id == row.id).values(code=code)
        )
        existing_codes.add(code)


def _next_unique_code(connection, hubs_table, existing_codes):
    while True:
        candidate = _generate_code()
        if candidate in existing_codes:
            continue
        exists = connection.execute(
            sa.select(hubs_table.c.id)
            .where(hubs_table.c.code == candidate)
            .limit(1)
        ).first()
        if exists:
            continue
        return candidate


def upgrade() -> None:
    op.add_column("hubs", sa.Column("code", sa.String(length=50), nullable=True))

    hubs_table = sa.table(
        "hubs",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String(length=50)),
    )

    connection = op.get_bind()
    _assign_missing_codes(connection, hubs_table)

    op.alter_column("hubs", "code", existing_type=sa.String(length=50), nullable=False)
    op.create_unique_constraint("uq_hubs_code", "hubs", ["code"])


def downgrade() -> None:
    op.drop_constraint("uq_hubs_code", "hubs", type_="unique")
    op.drop_column("hubs", "code")
