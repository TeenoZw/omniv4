"""Omni v4 shared business platform foundation models."""
from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models import Base, BaseModel


class Company(BaseModel):
    """Tenant/company profile for the Omni Business Platform."""

    __tablename__ = "v4_companies"

    name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=True)
    code = Column(String(64), nullable=False, unique=True, index=True)
    base_currency = Column(String(10), nullable=False, default="USD", server_default="USD")
    country = Column(String(120), nullable=True)
    tax_identifier = Column(String(120), nullable=True)
    fiscal_year_start_month = Column(Integer, nullable=False, default=1, server_default="1")
    is_active = Column(Boolean, nullable=False, default=True, server_default="true", index=True)
    settings = Column(JSON, nullable=False, default=dict)

    parties = relationship("Party", back_populates="company", cascade="all, delete-orphan")
    items = relationship("Item", back_populates="company", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="company", cascade="all, delete-orphan")
    warehouses = relationship("Warehouse", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Company {self.code}>"


class Party(BaseModel):
    """Shared customer, supplier, employee, contact, and organization record."""

    __tablename__ = "v4_parties"

    company_id = Column(Uuid(as_uuid=True), ForeignKey("v4_companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    party_type = Column(String(40), nullable=False, default="organization", server_default="organization", index=True)
    roles = Column(JSON, nullable=False, default=list)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(80), nullable=True)
    tax_identifier = Column(String(120), nullable=True)
    billing_address = Column(Text, nullable=True)
    shipping_address = Column(Text, nullable=True)
    status = Column(String(40), nullable=False, default="active", server_default="active", index=True)
    source_hub_id = Column(Uuid(as_uuid=True), ForeignKey("hubs.id"), nullable=True, index=True)
    extra_data = Column(JSON, nullable=False, default=dict)

    company = relationship("Company", back_populates="parties")
    source_hub = relationship("Hub")

    __table_args__ = (
        UniqueConstraint("company_id", "email", name="uq_v4_party_company_email"),
    )

    def __repr__(self) -> str:
        return f"<Party {self.name}>"


class Item(BaseModel):
    """Shared product, service, inventory item, fleet part, or billable service."""

    __tablename__ = "v4_items"

    company_id = Column(Uuid(as_uuid=True), ForeignKey("v4_companies.id", ondelete="CASCADE"), nullable=False, index=True)
    sku = Column(String(80), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    item_type = Column(String(40), nullable=False, default="product", server_default="product", index=True)
    category = Column(String(120), nullable=True, index=True)
    unit_of_measure = Column(String(40), nullable=False, default="each", server_default="each")
    is_stocked = Column(Boolean, nullable=False, default=False, server_default="false", index=True)
    is_serialized = Column(Boolean, nullable=False, default=False, server_default="false")
    is_active = Column(Boolean, nullable=False, default=True, server_default="true", index=True)
    sales_account_id = Column(Uuid(as_uuid=True), ForeignKey("v4_accounts.id"), nullable=True)
    purchase_account_id = Column(Uuid(as_uuid=True), ForeignKey("v4_accounts.id"), nullable=True)
    inventory_account_id = Column(Uuid(as_uuid=True), ForeignKey("v4_accounts.id"), nullable=True)
    source_hardware_id = Column(Integer, ForeignKey("hardware_inventory.id"), nullable=True, index=True)
    extra_data = Column(JSON, nullable=False, default=dict)

    company = relationship("Company", back_populates="items")
    sales_account = relationship("Account", foreign_keys=[sales_account_id])
    purchase_account = relationship("Account", foreign_keys=[purchase_account_id])
    inventory_account = relationship("Account", foreign_keys=[inventory_account_id])
    source_hardware = relationship("HardwareInventory")

    __table_args__ = (
        UniqueConstraint("company_id", "sku", name="uq_v4_item_company_sku"),
    )

    def __repr__(self) -> str:
        return f"<Item {self.sku}>"


class DocumentSequence(BaseModel):
    """Configurable numbering sequence for v4 business documents."""

    __tablename__ = "v4_document_sequences"

    company_id = Column(Uuid(as_uuid=True), ForeignKey("v4_companies.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(60), nullable=False)
    prefix = Column(String(20), nullable=False, default="", server_default="")
    next_number = Column(Integer, nullable=False, default=1, server_default="1")
    padding = Column(Integer, nullable=False, default=5, server_default="5")
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")

    company = relationship("Company")

    __table_args__ = (
        UniqueConstraint("company_id", "document_type", name="uq_v4_sequence_company_document_type"),
    )


class FiscalPeriod(BaseModel):
    """Accounting fiscal period for controlled posting and reporting."""

    __tablename__ = "v4_fiscal_periods"

    company_id = Column(Uuid(as_uuid=True), ForeignKey("v4_companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(40), nullable=False, default="open", server_default="open", index=True)

    company = relationship("Company")

    __table_args__ = (
        UniqueConstraint("company_id", "name", name="uq_v4_fiscal_period_company_name"),
    )


class Account(BaseModel):
    """Chart of accounts node."""

    __tablename__ = "v4_accounts"

    company_id = Column(Uuid(as_uuid=True), ForeignKey("v4_companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(40), nullable=False)
    name = Column(String(255), nullable=False)
    account_type = Column(String(40), nullable=False, index=True)
    parent_id = Column(Uuid(as_uuid=True), ForeignKey("v4_accounts.id"), nullable=True, index=True)
    is_control_account = Column(Boolean, nullable=False, default=False, server_default="false")
    is_active = Column(Boolean, nullable=False, default=True, server_default="true", index=True)

    company = relationship("Company", back_populates="accounts")
    parent = relationship("Account", remote_side="Account.id")

    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_v4_account_company_code"),
    )

    def __repr__(self) -> str:
        return f"<Account {self.code}>"


class BusinessDocument(BaseModel):
    """Shared document header for sales, purchasing, accounting, and operations."""

    __tablename__ = "v4_documents"

    company_id = Column(Uuid(as_uuid=True), ForeignKey("v4_companies.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(60), nullable=False, index=True)
    document_no = Column(String(80), nullable=False)
    status = Column(String(40), nullable=False, default="draft", server_default="draft", index=True)
    party_id = Column(Uuid(as_uuid=True), ForeignKey("v4_parties.id"), nullable=True, index=True)
    issue_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    currency = Column(String(10), nullable=False, default="USD", server_default="USD")
    subtotal = Column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    tax_total = Column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    discount_total = Column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    total = Column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    posted_at = Column(DateTime(timezone=True), nullable=True)
    source_enquiry_id = Column(Uuid(as_uuid=True), ForeignKey("enquiries.id"), nullable=True, index=True)
    source_hub_id = Column(Uuid(as_uuid=True), ForeignKey("hubs.id"), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=False, default=dict)

    company = relationship("Company")
    party = relationship("Party")
    lines = relationship("BusinessDocumentLine", back_populates="document", cascade="all, delete-orphan")
    source_enquiry = relationship("Enquiry")
    source_hub = relationship("Hub")

    __table_args__ = (
        UniqueConstraint("company_id", "document_no", name="uq_v4_document_company_no"),
    )

    def __repr__(self) -> str:
        return f"<BusinessDocument {self.document_no}>"


class BusinessDocumentLine(Base):
    """Line item for a v4 business document."""

    __tablename__ = "v4_document_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Uuid(as_uuid=True), ForeignKey("v4_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Uuid(as_uuid=True), ForeignKey("v4_items.id"), nullable=True, index=True)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(14, 4), nullable=False, default=1, server_default="1")
    unit_price = Column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    discount_amount = Column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    tax_amount = Column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    line_total = Column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    document = relationship("BusinessDocument", back_populates="lines")
    item = relationship("Item")


class JournalEntry(BaseModel):
    """Accounting journal entry header."""

    __tablename__ = "v4_journal_entries"

    company_id = Column(Uuid(as_uuid=True), ForeignKey("v4_companies.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_no = Column(String(80), nullable=False)
    entry_date = Column(Date, nullable=False, index=True)
    status = Column(String(40), nullable=False, default="draft", server_default="draft", index=True)
    memo = Column(Text, nullable=True)
    source_document_id = Column(Uuid(as_uuid=True), ForeignKey("v4_documents.id"), nullable=True, index=True)
    posted_at = Column(DateTime(timezone=True), nullable=True)

    company = relationship("Company")
    source_document = relationship("BusinessDocument")
    lines = relationship("JournalLine", back_populates="entry", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("company_id", "entry_no", name="uq_v4_journal_entry_company_no"),
    )

    def __repr__(self) -> str:
        return f"<JournalEntry {self.entry_no}>"


class JournalLine(Base):
    """Debit or credit line for a journal entry."""

    __tablename__ = "v4_journal_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    journal_entry_id = Column(Uuid(as_uuid=True), ForeignKey("v4_journal_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(Uuid(as_uuid=True), ForeignKey("v4_accounts.id"), nullable=False, index=True)
    party_id = Column(Uuid(as_uuid=True), ForeignKey("v4_parties.id"), nullable=True, index=True)
    debit = Column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    credit = Column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    memo = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account")
    party = relationship("Party")


class Warehouse(BaseModel):
    """Stock location for inventory and fleet parts."""

    __tablename__ = "v4_warehouses"

    company_id = Column(Uuid(as_uuid=True), ForeignKey("v4_companies.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(40), nullable=False)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true", index=True)

    company = relationship("Company", back_populates="warehouses")

    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_v4_warehouse_company_code"),
    )


class StockMovement(Base):
    """Event-based stock movement ledger."""

    __tablename__ = "v4_stock_movements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Uuid(as_uuid=True), ForeignKey("v4_companies.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(Uuid(as_uuid=True), ForeignKey("v4_items.id"), nullable=False, index=True)
    warehouse_id = Column(Uuid(as_uuid=True), ForeignKey("v4_warehouses.id"), nullable=False, index=True)
    movement_type = Column(String(60), nullable=False, index=True)
    movement_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    quantity = Column(Numeric(14, 4), nullable=False)
    unit_cost = Column(Numeric(14, 2), nullable=True)
    serial_number = Column(String(120), nullable=True, index=True)
    batch_number = Column(String(120), nullable=True, index=True)
    source_document_id = Column(Uuid(as_uuid=True), ForeignKey("v4_documents.id"), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    company = relationship("Company")
    item = relationship("Item")
    warehouse = relationship("Warehouse")
    source_document = relationship("BusinessDocument")
