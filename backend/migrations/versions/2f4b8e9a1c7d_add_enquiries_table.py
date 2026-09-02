"""add enquiries table

Revision ID: 2f4b8e9a1c7d
Revises: c1b3f7c1c6bf
Create Date: 2026-02-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2f4b8e9a1c7d"
down_revision: Union[str, Sequence[str], None] = "c1b3f7c1c6bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create enquiries table."""
    enquiry_status = postgresql.ENUM(
        "new",
        "quoted",
        "awaiting_payment",
        "onboarded",
        "closed_lost",
        name="enquiry_status",
        create_type=False,
    )
    customer_type = postgresql.ENUM(
        "individual",
        "business",
        name="enquiry_customer_type",
        create_type=False,
    )

    enquiry_status.create(op.get_bind(), checkfirst=True)
    customer_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "enquiries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("status", enquiry_status, nullable=False),
        sa.Column("customer_type", customer_type, nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=80), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column(
            "hardware_choices",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "add_ons",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("terms_accepted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("privacy_accepted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("quoted_monthly", sa.Numeric(10, 2), nullable=True),
        sa.Column("quoted_hardware_total", sa.Numeric(10, 2), nullable=True),
        sa.Column("quote_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_enquiries_status", "enquiries", ["status"], unique=False)
    op.create_index("ix_enquiries_email", "enquiries", ["email"], unique=False)


def downgrade() -> None:
    """Drop enquiries table."""
    op.drop_index("ix_enquiries_email", table_name="enquiries")
    op.drop_index("ix_enquiries_status", table_name="enquiries")
    op.drop_table("enquiries")

    op.execute("DROP TYPE IF EXISTS enquiry_status")
    op.execute("DROP TYPE IF EXISTS enquiry_customer_type")
