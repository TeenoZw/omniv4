# 32 - ERPNext Selective Adoption Plan

## Purpose

This document defines how Omni v4 should use ERPNext without blindly copying or rebuilding everything. ERPNext should provide the proven ERP backbone, while Omni should provide the differentiated fleet, field operations, telematics provider integration, tracker/SIM, customer operations, and usability layer.

The goal is selective adoption:

> Use ERPNext for generic ERP depth. Build Omni for fleet and operations depth.

Traceable execution tasks are tracked in `docs/33_omniv4_execution_backlog.md`.

## Local ERPNext Source Reviewed

ERPNext source is available locally at:

```text
/Users/h2o/erpnext-develop
```

Key files reviewed:

- `/Users/h2o/erpnext-develop/README.md`
- `/Users/h2o/erpnext-develop/license.txt`
- `/Users/h2o/erpnext-develop/pyproject.toml`
- `/Users/h2o/erpnext-develop/erpnext/hooks.py`
- `/Users/h2o/erpnext-develop/erpnext/modules.txt`
- Representative DocTypes under:
  - `erpnext/accounts/doctype`
  - `erpnext/selling/doctype`
  - `erpnext/buying/doctype`
  - `erpnext/stock/doctype`
  - `erpnext/assets/doctype`
  - `erpnext/crm/doctype`
  - `erpnext/maintenance/doctype`
  - `erpnext/projects/doctype`
  - `erpnext/support/doctype`

ERPNext is a Frappe app. Its business model is DocType-driven, not SQLAlchemy-driven. It already includes the ERP backbone Omni v4 needs: accounting, GL, customers, suppliers, items, warehouses, stock ledger, sales, purchasing, assets, maintenance, projects, support, and CRM.

## Licensing Note

ERPNext is licensed under GPLv3.

This does not block us from using it, but it does affect how we package, modify, host, and distribute Omni if Omni is built on ERPNext or includes ERPNext code.

Working rule:

- Treat ERPNext as an upstream open-source platform.
- Avoid copy-pasting ERPNext source into the current Omni FastAPI/Svelte app.
- Prefer building a separate Omni Frappe app installed alongside ERPNext.
- Get proper legal advice before commercial distribution, especially if distributing modified ERPNext or a combined work.

## Recommended Direction

Build Omni v4 as a custom Frappe app installed alongside ERPNext.

```text
Frappe Bench
|
+-- frappe
+-- erpnext
+-- omni_operations
```

ERPNext should own:

- Accounting
- General ledger
- Journal entries
- Bank accounts
- Receivables
- Payables
- Taxes
- Sales invoices
- Fiscalisation status and references through Omni
- Purchase invoices
- Customers
- Suppliers
- Items
- Warehouses
- Stock ledger
- Sales orders
- Purchase orders
- Delivery notes
- Purchase receipts
- Assets
- Depreciation
- Maintenance schedules
- Projects
- Support tickets
- CRM leads/opportunities where suitable

Omni should own:

- Fleet 360
- Vehicle 360
- Customer fleet view
- Telematics provider integration
- GPS asset sync
- Tracker inventory profile extensions
- SIM inventory profile extensions
- Tracker-to-vehicle assignment workflows
- Driver assignment workflows
- Fleet profitability dashboards
- Vehicle licence and insurance workflows
- Field technician installation workflows
- Maintenance workflows where ERPNext is too generic
- Fiscalisation provider integration for ZIMRA FDMS and possible third-party fiscalisation providers
- Zimbabwe/local fleet operating rules
- Simplified customer portal experience

## What We Should Not Take From ERPNext

We should not copy the whole ERPNext UI or expose every module by default.

Avoid:

- Manufacturing unless a customer specifically needs it later
- Quality management in the MVP
- EDI in the MVP
- Telephony in the MVP
- Shopping cart/e-commerce in the MVP
- Loyalty/POS in the MVP unless retail becomes a target segment
- Deep subcontracting in the MVP
- Complex banking automation in the first release
- Any ERPNext screen that adds complexity without helping the target Omni customer

Omni should not become a cluttered ERPNext rebrand. The product must remain focused on operations-heavy companies.

## Selective Adoption Matrix

| Omni Need | ERPNext Source | Adopt? | Approach |
| --- | --- | --- | --- |
| Company/Tenant | Setup `Company` | Yes | Use ERPNext `Company` as the business root. |
| Customer | Selling `Customer` | Yes | Use ERPNext Customer; add Omni fleet fields via custom fields/linked DocTypes. |
| Supplier | Buying `Supplier` | Yes | Use ERPNext Supplier. |
| Products/Services | Stock `Item` | Yes | Use ERPNext Item for products, services, trackers, SIMs, parts, subscriptions. |
| Warehouses | Stock `Warehouse` | Yes | Use ERPNext Warehouse for stock locations and workshops. |
| Stock Ledger | Stock Ledger Entry | Yes | Use ERPNext stock movement and valuation engine. |
| Chart of Accounts | Accounts `Account` | Yes | Use ERPNext chart of accounts. |
| General Ledger | Accounts `GL Entry` | Yes | Use ERPNext GL. Do not rebuild this. |
| Journal Entries | Accounts `Journal Entry` | Yes | Use ERPNext journal entry workflow. |
| Sales Quotes | Selling `Quotation` | Yes | Use ERPNext quotation; customize fleet quote templates. |
| Sales Orders | Selling `Sales Order` | Yes | Use ERPNext sales order. |
| Invoices | Accounts `Sales Invoice` | Yes | Use ERPNext invoices, PDF, taxes, payment status. |
| Fiscalisation | Sales Invoice + custom Omni fiscalisation DocTypes | Build Omni layer | Use ERPNext invoice as source document; submit fiscal payloads through provider adapters such as ZIMRA FDMS. |
| Receipts | Accounts `Payment Entry` | Yes | Use ERPNext payment entries. |
| Purchase Orders | Buying `Purchase Order` | Yes | Use ERPNext purchase workflow. |
| Supplier Bills | Accounts `Purchase Invoice` | Yes | Use ERPNext supplier invoice/payables. |
| Assets | Assets `Asset` | Yes | Use ERPNext Asset for company and customer assets where it fits. |
| Maintenance | Maintenance module | Partly | Use schedules/visits where suitable; add Omni work order depth for fleet. |
| CRM | CRM `Lead`, `Opportunity` | Partly | Use ERPNext pipeline primitives; simplify UI for Omni. |
| Projects | Projects module | Later | Adopt in Phase 3, not MVP. |
| HR | ERPNext/HRMS ecosystem | Later | Do not include in initial Omni v4 unless required. |
| Support | Support `Issue` | Yes | Use/support or extend for service tickets. |
| Fleet tracking | None / limited | Build Omni | This is Omni's core differentiator. |
| Telematics provider integration | Not core ERPNext | Build Omni | Dedicated provider-neutral integration DocTypes and provider-specific sync adapters. |
| Tracker/SIM operations | Item/Serial base only | Build Omni layer | Use ERPNext Item/Serial where useful; add Omni-specific assignment logic. |
| ZIMRA FDMS | Not core ERPNext | Build Omni layer | Dedicated fiscalisation DocTypes and ZIMRA adapter; store fiscal receipt, QR, fiscal day, and sync state against invoices. |

## Target Omni Frappe App

Recommended app name:

```text
omni_operations
```

Recommended modules inside the app:

```text
omni_operations
|
+-- fleet
+-- telematics
+-- tracker_inventory
+-- sim_inventory
+-- field_service
+-- customer_portal
+-- dashboards
+-- integrations
+-- setup
```

Recommended Omni DocTypes:

```text
Fleet Vehicle
Fleet Driver
Vehicle Assignment
Tracker Profile
SIM Profile
Tracker Installation
Telematics Provider Account
Telematics Unit Link
Telematics Sync Log
Fleet Contract
Fleet Subscription Profile
Fleet Maintenance Work Order
Fleet Fuel Log
Fleet Licence
Fleet Insurance
Fleet Profitability Snapshot
Customer Fleet Profile
```

Where possible, these DocTypes should link to ERPNext:

- `Company`
- `Customer`
- `Supplier`
- `Item`
- `Serial No`
- `Batch`
- `Warehouse`
- `Sales Invoice`
- `Sales Order`
- `Purchase Order`
- `Purchase Receipt`
- `Payment Entry`
- `Asset`
- `Project`
- `Issue`

## Architecture Options

### Option A - Custom Frappe App on ERPNext

This is the recommended path.

Pros:

- Uses ERPNext natively.
- Avoids rebuilding accounting, stock, and sales.
- Omni custom data lives inside the same permission, workflow, audit, report, and API ecosystem.
- Lower integration friction.

Cons:

- Requires learning Frappe/ERPNext development patterns.
- Current Svelte/FastAPI code becomes secondary or transitional.
- GPL/commercial packaging must be handled carefully.

### Option B - Keep Omni FastAPI/Svelte and Integrate ERPNext by API

This can work as a bridge, but should not be the long-term default.

Pros:

- Keeps current Omni UI/backend.
- Allows gradual adoption.
- Lower initial disruption.

Cons:

- Two systems of record risk.
- More sync complexity.
- More auth/session complexity.
- Harder to maintain financial correctness.

Use this only for transition or for a highly custom customer portal.

### Option C - Copy ERPNext Pieces Into Omni

Not recommended.

Reasons:

- ERPNext business logic is deep and interconnected.
- Copying selected Python files would break assumptions about Frappe, DocTypes, permissions, workflows, and database APIs.
- GPL obligations become messier.
- We would inherit complexity without the framework benefits.

## Recommended Execution Path

### Stage 1 - ERPNext Evaluation Bench

Goal: run ERPNext locally and confirm the modules we need.

Tasks:

- Set up a Frappe bench.
- Install ERPNext from `/Users/h2o/erpnext-develop`.
- Create a test site.
- Complete setup wizard for a Zimbabwe-based demo company.
- Configure base currency, fiscal year, chart of accounts, tax/VAT basics, warehouses, and item groups.
- Create sample customers, suppliers, items, trackers, SIMs, vehicles, invoices, purchases, and assets.

Output:

- A working ERPNext demo site.
- A list of DocTypes Omni will use unchanged.
- A list of DocTypes Omni will extend.
- A list of Omni-only DocTypes we must build.

### Stage 2 - Omni v3 to ERPNext Mapping

Goal: decide how current Omni data maps into ERPNext.

Mapping:

| Omni v3 | ERPNext / Omni v4 |
| --- | --- |
| Hub | Customer + Customer Fleet Profile |
| Hub membership | Contact/User/Portal User linkage |
| Enquiry | Lead or Opportunity |
| Vehicle asset | Fleet Vehicle, optionally ERPNext Asset |
| Hardware inventory | Item + Serial No + Tracker Profile |
| SIM inventory | Item + Serial No/Batch + SIM Profile |
| Hardware assignment | Tracker Installation / Vehicle Assignment |
| Technician job | Fleet Maintenance Work Order or Service Visit |
| Subscription | Subscription / Sales Invoice / Fleet Contract |
| Billing fields | Sales Invoice + Payment Entry + Customer balance |
| Compliance records | Keep in Omni or map to custom Governance DocTypes |
| Audit log | Use Frappe Version/Activity plus Omni audit where needed |

Output:

- Migration mapping document.
- Data cleanup checklist.
- Import templates for Customers, Items, Assets, Serial Nos, and Fleet Vehicles.

### Stage 3 - Build the Omni Custom App Skeleton

Goal: create `omni_operations` as the long-term Omni v4 home.

Tasks:

- Create new Frappe app.
- Add app metadata and modules.
- Install it alongside ERPNext.
- Add basic workspace: Omni Operations.
- Add roles:
  - Omni Fleet Manager
  - Omni Technician
  - Omni Customer Portal User
  - Omni Finance User
  - Omni Operations Admin
- Add custom fields to ERPNext DocTypes where needed.

Output:

- Installable Omni Frappe app.
- Basic module navigation.
- Role and permission structure.

### Stage 4 - Build Fleet Core

Goal: add the Omni-specific layer ERPNext does not provide.

Build first:

- Fleet Vehicle
- Fleet Driver
- Tracker Profile
- SIM Profile
- Tracker Installation
- Vehicle Assignment
- Customer Fleet Profile
- Telematics Provider Account
- Telematics Unit Link
- Telematics Sync Log

Must link to:

- ERPNext Customer
- ERPNext Item
- ERPNext Serial No
- ERPNext Warehouse
- ERPNext Asset where applicable

Output:

- Fleet 360 base.
- Customer fleet overview.
- Tracker/SIM visibility.
- Telematics provider mapping foundation.

### Stage 5 - Commercial Workflow

Goal: connect fleet operations to sales and accounting.

Use ERPNext for:

- Quotation
- Sales Order
- Sales Invoice
- Payment Entry
- Subscription where appropriate

Build Omni-specific helpers:

- Fleet quote template
- Tracker installation package
- Subscription/fleet contract view
- Customer 360 simplification
- Invoice/payment summary in Omni portal

Output:

- Enquiry to quote to invoice to payment flow.
- Fleet customer billing visibility.

### Stage 6 - Maintenance and Field Service

Goal: connect fleet service workflows to ERPNext stock and accounting.

Use ERPNext for:

- Item
- Warehouse
- Stock Entry
- Asset where suitable
- Sales Invoice if billable
- Purchase Invoice if supplier-backed

Build Omni-specific:

- Fleet Maintenance Work Order
- Technician assignment workflow
- Parts used from inventory
- Service outcome report
- Maintenance invoice trigger

Output:

- Maintenance workflow that consumes inventory and can generate invoices.

### Stage 7 - Customer Portal Strategy

Goal: keep the customer-facing experience outside ERPNext Desk while using ERPNext/Frappe as the secure business backend.

Options:

- Use ERPNext portal pages for invoices, quotes, orders, and support.
- Keep Svelte client portal as a polished Omni-facing portal.
- Hybrid: Svelte portal talks to ERPNext/Frappe APIs for customer-facing data.

Recommended:

- Use ERPNext/Frappe portal pages only for early validation and emergency fallback.
- Keep the Svelte public site and Svelte customer portal as separately deployable customer-facing apps.
- Build a narrow Frappe API adapter for the customer portal instead of exposing ERPNext Desk or broad DocType APIs.

Output:

- Portal decision.
- Customer login strategy.
- API/security plan.

## UI Execution Plan

ERPNext's default Desk UI is powerful but can feel broad and dense. Omni should simplify the experience around the workflows our users actually need.

### Admin / Internal UI

Start with ERPNext Desk and a custom Omni workspace.

Do:

- Create an Omni Operations workspace.
- Hide irrelevant modules for target roles.
- Use role-based workspaces.
- Create focused list views for Fleet Vehicles, Trackers, SIMs, Installations, Work Orders, and Customer Fleet Profiles.
- Add dashboards for fleet operations, billing attention, maintenance due, tracker status, and telematics sync health.

Do not:

- Expose every ERPNext module to normal users.
- Recreate the whole Svelte admin UI immediately.
- Over-customize ERPNext before workflow fit is proven.

### Customer UI

Customer-facing UI should be simpler than ERPNext Desk.

Customer portal should show:

- Fleet
- Vehicles
- Trackers
- Invoices
- Payments
- Quotes
- Support tickets
- Maintenance history
- Telematics/tracking access
- Documents

This should be a custom Svelte portal for the production experience. ERPNext portal pages can remain as a temporary validation/fallback layer while the Frappe API adapter is completed.

## What Happens to Current Omni v3 Code?

Current Omni v3 should not be deleted immediately.

Recommended handling:

- Keep v3 running as the reference implementation for fleet onboarding, tracker/SIM workflows, and the current customer portal.
- Stop expanding the custom `v4_*` SQLAlchemy foundation tables until we confirm the ERPNext direction.
- Treat the v4 SQLAlchemy foundation work as a design prototype, not the long-term ERP backbone.
- Reuse concepts from v3, but rebuild long-term ERP workflows in Frappe/ERPNext.
- Migrate data gradually after the ERPNext mapping is tested.

## First Concrete Execution Tasks

1. Create an ERPNext evaluation environment.
2. Create a Zimbabwe demo company.
3. Configure accounting basics.
4. Configure stock basics.
5. Create sample data:
   - Customer
   - Supplier
   - Fleet service item
   - Tracker item
   - SIM item
   - Warehouse
   - Vehicle asset
   - Sales invoice
   - Purchase order
6. Create `omni_operations` app skeleton.
7. Add Omni roles.
8. Add first Omni DocTypes:
   - Fleet Vehicle
   - Tracker Profile
   - SIM Profile
   - Telematics Unit Link
9. Create a Customer Fleet Profile view.
10. Validate one end-to-end flow:

```text
Lead / Customer
-> Fleet Quote
-> Sales Invoice
-> Payment
-> Tracker assigned
-> Vehicle linked to telematics provider
-> Customer Fleet view updated
```

## Success Criteria for the ERPNext Pivot

The ERPNext adoption is successful if:

- We do not rebuild accounting.
- We do not rebuild stock ledger.
- We do not rebuild sales and purchasing documents.
- Omni fleet workflows link cleanly to ERPNext Customers, Items, Invoices, Payments, Warehouses, and Assets.
- Normal users see a simplified Omni workspace rather than the whole ERPNext universe.
- Customer-facing workflows stay simple.
- Fleet remains Omni's unique value.
- The system can answer: what did this vehicle cost, what revenue did it generate, what customer owns it, what tracker is installed, and what invoices/payments are linked?
