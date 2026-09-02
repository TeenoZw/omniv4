"""Tests for Omni v4 foundation model wiring."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base
from app.models.v4_foundation import (
    Account,
    BusinessDocument,
    BusinessDocumentLine,
    Company,
    Item,
    JournalEntry,
    JournalLine,
    Party,
    StockMovement,
    Warehouse,
)


def test_v4_foundation_models_create_shared_business_graph():
    """The v4 primitives should persist as one connected business graph."""

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()
    try:
        company = Company(name="Omni Demo", code="OMNI-DEMO", base_currency="USD")
        db.add(company)
        db.flush()

        customer = Party(
            company_id=company.id,
            name="Acme Transport",
            party_type="organization",
            roles=["customer"],
            email="ops@acme.example",
        )
        revenue = Account(
            company_id=company.id,
            code="4000",
            name="Service Revenue",
            account_type="revenue",
        )
        receivables = Account(
            company_id=company.id,
            code="1100",
            name="Trade Receivables",
            account_type="asset",
            is_control_account=True,
        )
        tracker_service = Item(
            company_id=company.id,
            sku="SVC-FLEET-MONTHLY",
            name="Fleet monitoring monthly service",
            item_type="service",
            unit_of_measure="month",
            sales_account=revenue,
        )
        warehouse = Warehouse(company_id=company.id, code="MAIN", name="Main Warehouse")
        db.add_all([customer, revenue, receivables, tracker_service, warehouse])
        db.flush()

        invoice = BusinessDocument(
            company_id=company.id,
            document_type="sales_invoice",
            document_no="INV-00001",
            status="approved",
            party_id=customer.id,
            issue_date=date(2026, 7, 8),
            currency="USD",
            subtotal=Decimal("100.00"),
            total=Decimal("100.00"),
        )
        invoice.lines.append(
            BusinessDocumentLine(
                item_id=tracker_service.id,
                description="Fleet monitoring monthly service",
                quantity=Decimal("1"),
                unit_price=Decimal("100.00"),
                line_total=Decimal("100.00"),
            )
        )
        db.add(invoice)
        db.flush()

        journal = JournalEntry(
            company_id=company.id,
            entry_no="JE-00001",
            entry_date=date(2026, 7, 8),
            status="posted",
            source_document_id=invoice.id,
        )
        journal.lines.extend(
            [
                JournalLine(account_id=receivables.id, party_id=customer.id, debit=Decimal("100.00")),
                JournalLine(account_id=revenue.id, credit=Decimal("100.00")),
            ]
        )
        stock_event = StockMovement(
            company_id=company.id,
            item_id=tracker_service.id,
            warehouse_id=warehouse.id,
            movement_type="opening_balance",
            quantity=Decimal("0"),
            source_document_id=invoice.id,
        )
        db.add_all([journal, stock_event])
        db.commit()

        saved_invoice = db.query(BusinessDocument).filter_by(document_no="INV-00001").one()
        saved_journal = db.query(JournalEntry).filter_by(entry_no="JE-00001").one()
        saved_stock_event = db.query(StockMovement).one()

        assert saved_invoice.party.name == "Acme Transport"
        assert saved_invoice.lines[0].item.sku == "SVC-FLEET-MONTHLY"
        assert len(saved_journal.lines) == 2
        assert saved_journal.source_document.document_no == "INV-00001"
        assert saved_stock_event.source_document_id == saved_invoice.id
    finally:
        db.close()
