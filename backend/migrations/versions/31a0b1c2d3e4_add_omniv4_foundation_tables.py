"""add Omni v4 foundation tables

Revision ID: 31a0b1c2d3e4
Revises: f1a2b3c4d5e6
Create Date: 2026-07-08 12:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "31a0b1c2d3e4"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    inspector = inspect(op.get_bind())
    return table_name in set(inspector.get_table_names())


def _create_index_once(table_name: str, index_name: str, columns: list[str], unique: bool = False) -> None:
    inspector = inspect(op.get_bind())
    indexes = {index["name"] for index in inspector.get_indexes(table_name)}
    if index_name not in indexes:
        op.create_index(index_name, table_name, columns, unique=unique)


def upgrade() -> None:
    if not _table_exists("v4_companies"):
        op.create_table(
            "v4_companies",
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("legal_name", sa.String(length=255), nullable=True),
            sa.Column("code", sa.String(length=64), nullable=False),
            sa.Column("base_currency", sa.String(length=10), server_default="USD", nullable=False),
            sa.Column("country", sa.String(length=120), nullable=True),
            sa.Column("tax_identifier", sa.String(length=120), nullable=True),
            sa.Column("fiscal_year_start_month", sa.Integer(), server_default="1", nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
            sa.Column("settings", sa.JSON(), nullable=False),
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("code"),
        )
    _create_index_once("v4_companies", "ix_v4_companies_code", ["code"], unique=True)
    _create_index_once("v4_companies", "ix_v4_companies_is_active", ["is_active"])

    if not _table_exists("v4_parties"):
        op.create_table(
            "v4_parties",
            sa.Column("company_id", sa.Uuid(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("party_type", sa.String(length=40), server_default="organization", nullable=False),
            sa.Column("roles", sa.JSON(), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=True),
            sa.Column("phone", sa.String(length=80), nullable=True),
            sa.Column("tax_identifier", sa.String(length=120), nullable=True),
            sa.Column("billing_address", sa.Text(), nullable=True),
            sa.Column("shipping_address", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=40), server_default="active", nullable=False),
            sa.Column("source_hub_id", sa.Uuid(), nullable=True),
            sa.Column("extra_data", sa.JSON(), nullable=False),
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["company_id"], ["v4_companies.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["source_hub_id"], ["hubs.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("company_id", "email", name="uq_v4_party_company_email"),
        )
    _create_index_once("v4_parties", "ix_v4_parties_company_id", ["company_id"])
    _create_index_once("v4_parties", "ix_v4_parties_party_type", ["party_type"])
    _create_index_once("v4_parties", "ix_v4_parties_email", ["email"])
    _create_index_once("v4_parties", "ix_v4_parties_status", ["status"])
    _create_index_once("v4_parties", "ix_v4_parties_source_hub_id", ["source_hub_id"])

    if not _table_exists("v4_accounts"):
        op.create_table(
            "v4_accounts",
            sa.Column("company_id", sa.Uuid(), nullable=False),
            sa.Column("code", sa.String(length=40), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("account_type", sa.String(length=40), nullable=False),
            sa.Column("parent_id", sa.Uuid(), nullable=True),
            sa.Column("is_control_account", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["company_id"], ["v4_companies.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["parent_id"], ["v4_accounts.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("company_id", "code", name="uq_v4_account_company_code"),
        )
    _create_index_once("v4_accounts", "ix_v4_accounts_company_id", ["company_id"])
    _create_index_once("v4_accounts", "ix_v4_accounts_account_type", ["account_type"])
    _create_index_once("v4_accounts", "ix_v4_accounts_parent_id", ["parent_id"])
    _create_index_once("v4_accounts", "ix_v4_accounts_is_active", ["is_active"])

    if not _table_exists("v4_items"):
        op.create_table(
            "v4_items",
            sa.Column("company_id", sa.Uuid(), nullable=False),
            sa.Column("sku", sa.String(length=80), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("item_type", sa.String(length=40), server_default="product", nullable=False),
            sa.Column("category", sa.String(length=120), nullable=True),
            sa.Column("unit_of_measure", sa.String(length=40), server_default="each", nullable=False),
            sa.Column("is_stocked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("is_serialized", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
            sa.Column("sales_account_id", sa.Uuid(), nullable=True),
            sa.Column("purchase_account_id", sa.Uuid(), nullable=True),
            sa.Column("inventory_account_id", sa.Uuid(), nullable=True),
            sa.Column("source_hardware_id", sa.Integer(), nullable=True),
            sa.Column("extra_data", sa.JSON(), nullable=False),
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["company_id"], ["v4_companies.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["inventory_account_id"], ["v4_accounts.id"]),
            sa.ForeignKeyConstraint(["purchase_account_id"], ["v4_accounts.id"]),
            sa.ForeignKeyConstraint(["sales_account_id"], ["v4_accounts.id"]),
            sa.ForeignKeyConstraint(["source_hardware_id"], ["hardware_inventory.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("company_id", "sku", name="uq_v4_item_company_sku"),
        )
    _create_index_once("v4_items", "ix_v4_items_company_id", ["company_id"])
    _create_index_once("v4_items", "ix_v4_items_item_type", ["item_type"])
    _create_index_once("v4_items", "ix_v4_items_category", ["category"])
    _create_index_once("v4_items", "ix_v4_items_is_stocked", ["is_stocked"])
    _create_index_once("v4_items", "ix_v4_items_is_active", ["is_active"])
    _create_index_once("v4_items", "ix_v4_items_source_hardware_id", ["source_hardware_id"])

    if not _table_exists("v4_document_sequences"):
        op.create_table(
            "v4_document_sequences",
            sa.Column("company_id", sa.Uuid(), nullable=False),
            sa.Column("document_type", sa.String(length=60), nullable=False),
            sa.Column("prefix", sa.String(length=20), server_default="", nullable=False),
            sa.Column("next_number", sa.Integer(), server_default="1", nullable=False),
            sa.Column("padding", sa.Integer(), server_default="5", nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["company_id"], ["v4_companies.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("company_id", "document_type", name="uq_v4_sequence_company_document_type"),
        )
    _create_index_once("v4_document_sequences", "ix_v4_document_sequences_company_id", ["company_id"])

    if not _table_exists("v4_fiscal_periods"):
        op.create_table(
            "v4_fiscal_periods",
            sa.Column("company_id", sa.Uuid(), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("start_date", sa.Date(), nullable=False),
            sa.Column("end_date", sa.Date(), nullable=False),
            sa.Column("status", sa.String(length=40), server_default="open", nullable=False),
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["company_id"], ["v4_companies.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("company_id", "name", name="uq_v4_fiscal_period_company_name"),
        )
    _create_index_once("v4_fiscal_periods", "ix_v4_fiscal_periods_company_id", ["company_id"])
    _create_index_once("v4_fiscal_periods", "ix_v4_fiscal_periods_status", ["status"])

    if not _table_exists("v4_documents"):
        op.create_table(
            "v4_documents",
            sa.Column("company_id", sa.Uuid(), nullable=False),
            sa.Column("document_type", sa.String(length=60), nullable=False),
            sa.Column("document_no", sa.String(length=80), nullable=False),
            sa.Column("status", sa.String(length=40), server_default="draft", nullable=False),
            sa.Column("party_id", sa.Uuid(), nullable=True),
            sa.Column("issue_date", sa.Date(), nullable=True),
            sa.Column("due_date", sa.Date(), nullable=True),
            sa.Column("currency", sa.String(length=10), server_default="USD", nullable=False),
            sa.Column("subtotal", sa.Numeric(14, 2), server_default="0", nullable=False),
            sa.Column("tax_total", sa.Numeric(14, 2), server_default="0", nullable=False),
            sa.Column("discount_total", sa.Numeric(14, 2), server_default="0", nullable=False),
            sa.Column("total", sa.Numeric(14, 2), server_default="0", nullable=False),
            sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("source_enquiry_id", sa.Uuid(), nullable=True),
            sa.Column("source_hub_id", sa.Uuid(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("extra_data", sa.JSON(), nullable=False),
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["company_id"], ["v4_companies.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["party_id"], ["v4_parties.id"]),
            sa.ForeignKeyConstraint(["source_enquiry_id"], ["enquiries.id"]),
            sa.ForeignKeyConstraint(["source_hub_id"], ["hubs.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("company_id", "document_no", name="uq_v4_document_company_no"),
        )
    _create_index_once("v4_documents", "ix_v4_documents_company_id", ["company_id"])
    _create_index_once("v4_documents", "ix_v4_documents_document_type", ["document_type"])
    _create_index_once("v4_documents", "ix_v4_documents_status", ["status"])
    _create_index_once("v4_documents", "ix_v4_documents_party_id", ["party_id"])
    _create_index_once("v4_documents", "ix_v4_documents_source_enquiry_id", ["source_enquiry_id"])
    _create_index_once("v4_documents", "ix_v4_documents_source_hub_id", ["source_hub_id"])

    if not _table_exists("v4_document_lines"):
        op.create_table(
            "v4_document_lines",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("document_id", sa.Uuid(), nullable=False),
            sa.Column("item_id", sa.Uuid(), nullable=True),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("quantity", sa.Numeric(14, 4), server_default="1", nullable=False),
            sa.Column("unit_price", sa.Numeric(14, 2), server_default="0", nullable=False),
            sa.Column("discount_amount", sa.Numeric(14, 2), server_default="0", nullable=False),
            sa.Column("tax_amount", sa.Numeric(14, 2), server_default="0", nullable=False),
            sa.Column("line_total", sa.Numeric(14, 2), server_default="0", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["document_id"], ["v4_documents.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["item_id"], ["v4_items.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_once("v4_document_lines", "ix_v4_document_lines_document_id", ["document_id"])
    _create_index_once("v4_document_lines", "ix_v4_document_lines_item_id", ["item_id"])

    if not _table_exists("v4_journal_entries"):
        op.create_table(
            "v4_journal_entries",
            sa.Column("company_id", sa.Uuid(), nullable=False),
            sa.Column("entry_no", sa.String(length=80), nullable=False),
            sa.Column("entry_date", sa.Date(), nullable=False),
            sa.Column("status", sa.String(length=40), server_default="draft", nullable=False),
            sa.Column("memo", sa.Text(), nullable=True),
            sa.Column("source_document_id", sa.Uuid(), nullable=True),
            sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["company_id"], ["v4_companies.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["source_document_id"], ["v4_documents.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("company_id", "entry_no", name="uq_v4_journal_entry_company_no"),
        )
    _create_index_once("v4_journal_entries", "ix_v4_journal_entries_company_id", ["company_id"])
    _create_index_once("v4_journal_entries", "ix_v4_journal_entries_entry_date", ["entry_date"])
    _create_index_once("v4_journal_entries", "ix_v4_journal_entries_status", ["status"])
    _create_index_once("v4_journal_entries", "ix_v4_journal_entries_source_document_id", ["source_document_id"])

    if not _table_exists("v4_journal_lines"):
        op.create_table(
            "v4_journal_lines",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("journal_entry_id", sa.Uuid(), nullable=False),
            sa.Column("account_id", sa.Uuid(), nullable=False),
            sa.Column("party_id", sa.Uuid(), nullable=True),
            sa.Column("debit", sa.Numeric(14, 2), server_default="0", nullable=False),
            sa.Column("credit", sa.Numeric(14, 2), server_default="0", nullable=False),
            sa.Column("memo", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["account_id"], ["v4_accounts.id"]),
            sa.ForeignKeyConstraint(["journal_entry_id"], ["v4_journal_entries.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["party_id"], ["v4_parties.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_once("v4_journal_lines", "ix_v4_journal_lines_journal_entry_id", ["journal_entry_id"])
    _create_index_once("v4_journal_lines", "ix_v4_journal_lines_account_id", ["account_id"])
    _create_index_once("v4_journal_lines", "ix_v4_journal_lines_party_id", ["party_id"])

    if not _table_exists("v4_warehouses"):
        op.create_table(
            "v4_warehouses",
            sa.Column("company_id", sa.Uuid(), nullable=False),
            sa.Column("code", sa.String(length=40), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("location", sa.String(length=255), nullable=True),
            sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["company_id"], ["v4_companies.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("company_id", "code", name="uq_v4_warehouse_company_code"),
        )
    _create_index_once("v4_warehouses", "ix_v4_warehouses_company_id", ["company_id"])
    _create_index_once("v4_warehouses", "ix_v4_warehouses_is_active", ["is_active"])

    if not _table_exists("v4_stock_movements"):
        op.create_table(
            "v4_stock_movements",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("company_id", sa.Uuid(), nullable=False),
            sa.Column("item_id", sa.Uuid(), nullable=False),
            sa.Column("warehouse_id", sa.Uuid(), nullable=False),
            sa.Column("movement_type", sa.String(length=60), nullable=False),
            sa.Column("movement_date", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("quantity", sa.Numeric(14, 4), nullable=False),
            sa.Column("unit_cost", sa.Numeric(14, 2), nullable=True),
            sa.Column("serial_number", sa.String(length=120), nullable=True),
            sa.Column("batch_number", sa.String(length=120), nullable=True),
            sa.Column("source_document_id", sa.Uuid(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["company_id"], ["v4_companies.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["item_id"], ["v4_items.id"]),
            sa.ForeignKeyConstraint(["source_document_id"], ["v4_documents.id"]),
            sa.ForeignKeyConstraint(["warehouse_id"], ["v4_warehouses.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    _create_index_once("v4_stock_movements", "ix_v4_stock_movements_company_id", ["company_id"])
    _create_index_once("v4_stock_movements", "ix_v4_stock_movements_item_id", ["item_id"])
    _create_index_once("v4_stock_movements", "ix_v4_stock_movements_warehouse_id", ["warehouse_id"])
    _create_index_once("v4_stock_movements", "ix_v4_stock_movements_movement_type", ["movement_type"])
    _create_index_once("v4_stock_movements", "ix_v4_stock_movements_movement_date", ["movement_date"])
    _create_index_once("v4_stock_movements", "ix_v4_stock_movements_serial_number", ["serial_number"])
    _create_index_once("v4_stock_movements", "ix_v4_stock_movements_batch_number", ["batch_number"])
    _create_index_once("v4_stock_movements", "ix_v4_stock_movements_source_document_id", ["source_document_id"])


def downgrade() -> None:
    for table_name in [
        "v4_stock_movements",
        "v4_warehouses",
        "v4_journal_lines",
        "v4_journal_entries",
        "v4_document_lines",
        "v4_documents",
        "v4_fiscal_periods",
        "v4_document_sequences",
        "v4_items",
        "v4_accounts",
        "v4_parties",
        "v4_companies",
    ]:
        if _table_exists(table_name):
            op.drop_table(table_name)
