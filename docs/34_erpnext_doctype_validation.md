# 34 - ERPNext DocType Validation for Omni v4

## Purpose

This document records the first validated ERPNext DocType boundaries for Omni v4.

Principle:

> ERPNext owns standard ERP transactions. Omni owns fleet-specific operations, telematics provider integration, tracker/SIM lifecycle, Fleet 360 views, and simplified workflows.

Validation site:

- Bench: `erpnext-eval/frappe_docker/development/frappe-bench`
- Site: `development.localhost`
- Frappe: `15.118.0`
- ERPNext: `15.119.2`
- Company: `Omni Demo Zimbabwe`

## Validated ERPNext DocTypes

These DocTypes were created or used successfully in the evaluation site.

| Area | ERPNext DocType | Sample Record | Omni Decision |
| --- | --- | --- | --- |
| Company setup | Company | `Omni Demo Zimbabwe` | Use unchanged as the legal/business entity. |
| Accounting setup | Fiscal Year | `2026` | Use unchanged. |
| Accounting setup | Account | `Debtors - ODZ`, `Creditors - ODZ`, `Omni Demo Bank - ODZ` | Use unchanged; configure carefully per deployment. |
| Banking | Payment Entry | `ACC-PAY-2026-00001`, `ACC-PAY-2026-00002` | Use unchanged; expose through simplified Omni finance views when needed. |
| Customers | Customer | `Acme Logistics Zimbabwe` | Use as the source customer record; extend/link from Omni Customer Fleet Profile. |
| Suppliers | Supplier | `Harare Tracker Supplies` | Use unchanged for purchasing. |
| Inventory | Item | `TRACKER-HW-4G`, `SIM-IOT`, `RELAY-12V` | Use for saleable/purchasable stock; link Tracker/SIM profiles to Item and later Serial No. |
| Inventory | Warehouse | `Main Fleet Stock - ODZ`, `Technician Stock - ODZ`, `Faulty Returns - ODZ` | Use unchanged; Omni UI should present these as operational stock locations. |
| Inventory | Stock Entry | `MAT-STE-2026-00001` | Use for stock adjustments/receipts/transfers; hide complexity behind simple flows. |
| Sales | Quotation | `SAL-QTN-2026-00001` | Use for commercial quoting; customize print/templates and fleet service bundles. |
| Sales | Sales Invoice | `ACC-SINV-2026-00001` | Use as the accounting invoice; link to Fleet Contract/Profile. |
| Purchasing | Purchase Order | `PUR-ORD-2026-00001` | Use unchanged for supplier ordering. |
| Purchasing | Purchase Receipt | `MAT-PRE-2026-00001` | Use for goods received. |
| Purchasing | Purchase Invoice | `ACC-PINV-2026-00001` | Use for supplier bills. |
| Assets | Asset | `ACC-ASS-2026-00001` | Use for formal asset register; Omni Fleet Vehicle remains a richer operational record. |
| Support | Issue | `ISS-2026-00001` | Use for support tickets; link to Customer, Vehicle, Tracker, and telematics context through Omni custom fields. |

## Use Unchanged

Use these ERPNext DocTypes directly with configuration, permissions, print formats, and maybe light custom fields:

- Company
- Fiscal Year
- Account
- Payment Entry
- Supplier
- Warehouse
- Stock Entry
- Purchase Order
- Purchase Receipt
- Purchase Invoice

## Extend Or Link

Use these ERPNext DocTypes as canonical ERP records, but attach Omni-specific context:

- Customer
  - Link to Customer Fleet Profile.
  - Show fleet, invoices, payments, tickets, contracts, vehicles, trackers, SIMs, and telematics provider accounts.
- Item
  - Link tracker hardware, SIM cards, relays, and service items into Omni workflows.
  - Later validate Serial No usage for individual tracker IMEIs and SIM ICCIDs.
- Quotation
  - Add fleet-specific templates and service bundles.
  - Link generated quotations to CRM opportunities and customer fleet profiles.
- Sales Invoice
  - Link invoices to Fleet Contract/Profile and possibly Vehicle/Tracker subscriptions.
- Asset
  - Use for depreciation and formal asset register.
  - Do not force operational vehicle lifecycle into Asset alone.
- Issue
  - Extend with vehicle, tracker, SIM, telematics unit, priority, and maintenance context.

## Build As Omni Custom DocTypes

These should be created in the `omni_operations` app rather than forced into ERPNext standard DocTypes:

- Fleet Vehicle
- Fleet Driver
- Tracker Profile
- SIM Profile
- Tracker Installation
- Telematics Provider Account
- Telematics Unit Link
- Telematics Sync Log
- Customer Fleet Profile
- Fleet Contract
- Fleet Maintenance Work Order

## Avoid For MVP

Do not expose these ERPNext areas in the first Omni v4 MVP unless a workflow requires them:

- Manufacturing
- POS
- Payroll
- Full project accounting
- Advanced budgeting
- Complex regional tax automation beyond the first Zimbabwe demo setup

## UI Implications

ERPNext Desk is powerful, but not simple enough to be the first user experience for fleet operators.

Recommended MVP UI split:

- Internal finance/admin users can use ERPNext Desk for accounting, stock, sales, purchasing, and master data.
- Operations users should use an Omni workspace with fewer entry points:
  - Fleet
  - Installations
  - Trackers
  - SIMs
  - Telematics Sync
  - Maintenance
  - Customer Fleet 360
- Customer users should not see ERPNext Desk. They should get a focused portal showing:
  - Fleet
  - Vehicles
  - Invoices
  - Payments
  - Support tickets
  - Tracking handoff/status

## Next Decision

Proceed to `C-001`: create the `omni_operations` Frappe app skeleton in the evaluation bench.

The app should start small:

- App metadata
- Modules
- Roles
- Fixtures structure
- Empty DocType placeholders only after the first app install is verified
