# 31 - Omni v4 Work Plan

## Purpose

Omni v4 will evolve the current Omni Logistics system into the **Omni Business Platform**: an operations-first business platform where fleet management remains the flagship module, but accounting, inventory, sales, purchasing, CRM, maintenance, assets, HR, projects, reports, and administration all work from one shared data model.

This document is the guiding plan for the v4 transition. It records the product direction, the gaps in the current v3 system, the target architecture, the phased delivery plan, and the UI principles that should keep the platform simple and usable as it grows.

## Product Positioning

### Current v3 Position

Omni v3 is primarily a fleet operations and onboarding platform. It currently supports:

- Customer enquiry and quote intake
- Hub/customer provisioning
- User, role, and hub membership management
- Customer portal login
- Billing status and subscription dates
- Vehicle and asset records
- Hardware tracker inventory
- SIM inventory
- Device and SIM assignment workflows
- Technician job cards
- Compliance registers
- Audit trail and admin activity logging
- Public marketing site
- Customer portal pages for assets, billing, support, settings, and security

This is a strong operational base and should not be discarded.

### v4 Position

Omni v4 should be positioned as:

> An operations-first business platform for companies that manage vehicles, assets, field work, stock, customers, suppliers, and money in one place.

The product should not try to compete head-on with generic ERP platforms as a broad, feature-for-feature clone. Omni should win by integrating business operations deeply with fleet, assets, maintenance, inventory, billing, and accounting.

Fleet management remains the flagship module, but it becomes one part of a wider business platform.

```text
Omni Business Platform
|
+-- Fleet Management
+-- Accounting
+-- Inventory
+-- Sales
+-- Purchasing
+-- CRM
+-- HR
+-- Projects
+-- Assets
+-- Maintenance
+-- Reports
+-- Administration
```

## Strategic Principle

The most important v4 principle is:

> Build around one shared business data model from day one.

Every module should use the same customers, suppliers, contacts, products, services, warehouses, users, documents, and accounting engine. This prevents CRM, fleet, sales, accounting, and inventory from becoming separate islands.

## Product Entry Points

Omni v4 should have three immediate entry points and one future partner entry point, all powered by the same platform but presented differently for each audience:

| Entry point | Domain | Audience | Purpose |
| --- | --- | --- | --- |
| Public website | `www.omnilogistics.co.zw` | Prospects, customers, partners | A separately deployable Svelte public site that explains Omni Logistics, communicates value, captures enquiries, and guides users into the customer portal. |
| Customer portal | `www.omnilogistics.co.zw/portal` or a dedicated portal deployment | Existing customers | A separately deployable Svelte customer app that lets customers view their fleet, tracker status, invoices, documents, contracts, maintenance updates, and support requests without seeing ERPNext Desk. |
| Internal admin app | `admin.omnilogistics.co.zw` | Directors, operations staff, technicians, finance/admin users | The Frappe/ERPNext admin app for managing the Omni Business Platform through the focused Omni workspace and approved ERPNext back-office screens. |
| Partner portal | `partners.omnilogistics.co.zw` | Future certified installers, sales/install partners, Gold Partners, and regional partners | A future Svelte partner app for partner onboarding, assigned jobs, installation evidence, activation status, stock visibility, support/warranty history, and commission visibility. |

Rules:

- The public website and customer portal should feel like one customer-facing experience.
- The customer portal should be an extension of the public website, not a separate-looking back-office app.
- The admin app should remain on `admin.omnilogistics.co.zw`.
- ERPNext Desk complexity should never be the first impression on `www.omnilogistics.co.zw`.
- Login redirects should send staff to the admin app and customers back into the public-site portal experience.
- Public website code should not live inside Frappe templates long-term. Frappe website pages are acceptable only as a temporary local preview or fallback.
- Customer portal UI should call a narrow Frappe API adapter, not generic ERPNext Desk routes.
- Partner portal work should wait until internal onboarding, public enquiry routing, guided installation, customer portal detail/tickets, and role work queues are reliable.
- Partners should not receive broad ERPNext Desk, Wialon/provider administration, or master credential access for normal daily work.

## Omni v3 UI Inheritance

Omni v4 should feel like an upgrade of Omni v3, not a generic ERPNext reskin.

Carry forward these v3 UI patterns:

- Soft cyan/blue operational shell backgrounds.
- Glass-style panels with restrained shadows.
- Compact metric cards for fleet, billing, support, and device status.
- Customer-facing pages that read like Omni Eye, not ERPNext Desk.
- Rounded navigation rails, focused work areas, and clear action buttons.
- Marketing language around managed fleet intelligence, local support, onboarding, billing, governance, and telematics access.

Apply them carefully:

- Use Svelte as the long-term public/customer UI home.
- Use Frappe CSS only as a bridge for admin Desk polish and temporary Frappe portal pages.
- Do not copy old v3 backend assumptions into v4; only reuse visual language, UX patterns, and customer-facing concepts.
- Keep admin screens denser and calmer than the public website because directors and staff will use them repeatedly.

## Deployable App Split

Omni v4 should run as separate deployable apps:

| App | Codebase | Local port | Production host | Responsibility |
| --- | --- | --- | --- | --- |
| Public Site | `client-web` | `5174` | `www.omnilogistics.co.zw` | Marketing pages, enquiry entry, public policy pages, portal handoff. |
| Customer Portal | `client-web` portal surface, later separable into its own package if it grows | `5175` | `www.omnilogistics.co.zw/portal` or a portal-specific host | Customer dashboard, fleet view, support, documents, invoices, tracking handoff. |
| Admin App | Frappe bench with `erpnext` + `omni_operations` | `8000` locally | `admin.omnilogistics.co.zw` | ERP backbone, Omni Operations workspace, internal workflows, accounting, stock, billing, fiscalisation, telematics sync. |
| Partner Portal | Future Svelte partner surface | TBD | `partners.omnilogistics.co.zw` | Partner onboarding, assigned field work, installation evidence, activation approval, stock visibility, support/warranty history, and commission visibility. |

The local helper compose file `docker-compose.omniv4-surfaces.yml` starts the two customer-facing Svelte surfaces independently from the Frappe admin app. Frappe remains the source of truth for business data and exposes only the API endpoints those surfaces need.

## ERPNext Direction

After reviewing the local ERPNext source under `/Users/h2o/erpnext-develop`, the preferred v4 execution path is to use ERPNext selectively as the ERP backbone instead of rebuilding generic ERP primitives inside the current FastAPI/Svelte application.

ERPNext should provide the backbone for accounting, stock, selling, buying, customers, suppliers, items, warehouses, invoices, payments, assets, projects, support, and common ERP reports. Omni should provide the differentiated fleet, telematics provider, tracker/SIM, field operations, customer fleet, and usability layer.

See `docs/32_erpnext_selective_adoption_plan.md` for the execution plan.

Working rule:

- Do not copy ERPNext source into Omni.
- Do not expose the entire ERPNext surface by default.
- Build only the Omni-specific layer needed for fleet and operations.
- Stop expanding custom `v4_*` SQLAlchemy tables until the ERPNext adoption path is validated.
- Treat existing `v4_*` foundation work as a design prototype unless we decide not to proceed with ERPNext.

## Zimbabwe Fiscalisation Direction

Omni v4 should plan for ZIMRA FDMS fiscalisation as a core commercial and compliance capability for Zimbabwe deployments.

ZIMRA supports Virtual Fiscalisation through software based Virtual Fiscal Devices / API integration with the Fiscalisation Data Management System (FDMS). ZIMRA states that the Virtual Fiscalisation API can be accessed by taxpayers free of charge from the ZIMRA website. That does not mean the whole compliance project is free: implementation, testing, onboarding, approval, operational support, and any third-party provider costs still need to be planned.

Recommended approach:

- Build a provider-neutral fiscalisation layer, similar to the telematics layer.
- Treat ZIMRA FDMS as the first fiscal provider adapter, not as hard-coded invoice logic.
- Integrate at ERPNext `Sales Invoice`, `Credit Note`, and commercial workflow boundaries.
- Store fiscal status, fiscal receipt number, fiscal day/counter state, QR code data, FDMS signature, request/response logs, and errors.
- Keep ZIMRA credentials, device registration data, and activation keys separate from ordinary invoice data.
- Update print formats so fiscal invoices include required ZIMRA fiscal details and QR code data.
- Start with test/sandbox/onboarding mode before live fiscalisation.

Proposed Omni fiscalisation DocTypes:

- `Fiscal Provider Account`
- `Fiscal Device`
- `Fiscal Day`
- `Fiscal Document`
- `Fiscal Sync Log`

Commercial note:

- Direct ZIMRA FDMS API access is the lowest long-term software-cost path if we build and maintain the integration ourselves.
- Third-party fiscalisation providers may reduce compliance and onboarding effort, but usually add subscription, setup, or transaction costs.
- Hardware fiscal devices remain an alternative where API integration is not appropriate.

## Current Gaps

The current system has useful fleet and operations primitives, but it does not yet have a true ERP backbone.

Missing or immature areas include:

- Chart of accounts
- Journal entries
- General ledger
- Trial balance
- Balance sheet
- Income statement
- Cash flow statement
- Bank accounts
- Bank reconciliation
- Petty cash
- Budgets
- Customer statements
- Receipts
- Credit notes
- Customer aging
- Supplier bills
- Supplier payments
- Outstanding payables
- Products and services catalog
- Units of measure
- Product categories and brands
- Serial number and batch number support beyond tracker/SIM inventory
- Warehouses and bin locations
- Stock transfers
- Stock counts
- Stock adjustments
- Reorder levels
- Sales quotations as accounting-ready documents
- Sales orders
- Delivery notes
- Invoices
- Fiscalisation / ZIMRA FDMS integration
- Purchase requests
- RFQs
- Purchase orders
- Goods received notes
- Supplier invoices
- VAT/tax engine
- Discounts and partial payments
- Shared customer/supplier/contact model
- Document numbering and approval workflow
- Full CRM pipeline
- Maintenance work orders tied to inventory and invoicing
- Asset depreciation schedules
- HR, payroll, leave, attendance, and departments
- Project budgets, expenses, tasks, and project invoicing
- Document storage for contracts, licences, insurance, registrations, tax certificates, purchase orders, and invoices

## v4 Foundation Model

The center of v4 should not be the current hub model. Hubs are useful for fleet/customer grouping, but the business platform needs more universal primitives.

The v4 center should be:

```text
Company / Tenant
Party
Item
Document
Ledger
Stock Movement
Asset
User
```

### Shared Models

#### Company / Tenant

Represents the business using Omni. This enables Omni to serve multiple companies cleanly later.

Omni implementation decision:

- For the current Omni deployment, the accounting company is `Omni Industrial Solutions`.
- Customer hubs are not ERPNext Companies. They are ERPNext Customers with Omni fleet profiles, portal users, vehicles, contracts, tickets, and billing history linked to them.
- Do not create one Company per hub/customer. A new Company should only exist for a real legal/accounting entity that needs its own books, fiscal settings, tax setup, and reports.
- Operational documents may still carry a `company` field because ERPNext needs it for accounting and stock valuation, but that field should resolve to Omni's accounting company unless a genuine new legal entity is introduced.

Key needs:

- Company profile
- Base currency
- Tax settings
- Fiscal year settings
- Module settings
- Numbering settings
- Users and roles

#### Party

One shared model for people and organizations.

Party roles can include:

- Customer
- Supplier
- Employee
- Driver
- Technician
- Contact
- Organization

This avoids duplicate records where the same business is a customer in sales, a debtor in accounting, and an organization in CRM.

#### Item

One shared model for anything sold, bought, stocked, consumed, or billed.

Item types can include:

- Product
- Service
- Inventory item
- Fleet part
- Billable service
- Subscription item
- Asset component

#### Document

One shared document framework should power sales, purchasing, invoicing, and inventory documents.

Document types should include:

- Quotation
- Sales order
- Delivery note
- Invoice
- Receipt
- Credit note
- Purchase request
- RFQ
- Purchase order
- Goods received note
- Supplier bill
- Supplier payment
- Stock adjustment
- Stock transfer
- Maintenance work order

Each document should support:

- Numbering
- Draft/approved/posted/cancelled lifecycle
- Linked party
- Line items
- Taxes
- Discounts
- Attachments
- Notes
- Audit trail
- Accounting posting status where applicable

#### Ledger

The accounting ledger should be the financial source of truth.

Core models:

- Account
- Journal entry
- Journal line
- Fiscal period
- Tax rate
- Currency
- Bank account
- Payment
- Allocation

#### Stock Movement

Inventory should be event-based. Stock quantities should be derived from stock movements rather than manually overwritten wherever possible.

Movement types:

- Purchase receipt
- Sales delivery
- Transfer
- Adjustment
- Return
- Maintenance consumption
- Opening balance

#### Asset

Assets should include vehicles and non-vehicle assets.

Asset types:

- Vehicles
- Trailers
- Machinery
- Laptops
- Generators
- UPS systems
- Tools
- Office equipment
- Trackable customer assets

Assets should support:

- Ownership
- Location
- Depreciation
- Service history
- Insurance
- Licences
- Documents
- Assigned users/drivers
- Related costs and revenue

## Target Backend Architecture

Use a modular monolith first. This keeps development faster and data consistency simpler while allowing clean module boundaries.

Recommended structure:

```text
backend/app/modules
+-- identity
+-- parties
+-- accounting
+-- inventory
+-- sales
+-- purchasing
+-- fleet
+-- maintenance
+-- crm
+-- hr
+-- projects
+-- documents
+-- reports
+-- administration
```

Each module should own:

- Models
- Schemas
- Routes
- Services
- Permission definitions
- Tests

Shared infrastructure should live outside modules:

- Database/session setup
- Authentication
- Authorization
- Audit logging
- Numbering
- File storage
- Background jobs
- Notifications
- Email
- PDF generation
- Import/export utilities

## Accounting Posting Principle

Accounting must be the backbone of v4.

Operational modules should not directly manipulate account balances. They should create accounting-ready documents that post through a controlled posting engine.

Examples:

```text
Sales invoice approved
-> journal entry posted
-> receivables increased
-> revenue and tax recorded
```

```text
Customer payment captured
-> journal entry posted
-> bank/cash increased
-> receivable reduced
```

```text
Goods received
-> stock movement recorded
-> inventory value updated if valuation is enabled
```

```text
Maintenance work order completed
-> parts consumed from inventory
-> customer invoice generated if billable
-> accounting updated when invoice is posted
```

## Product Modules

### Fleet Management

Fleet remains the flagship feature.

Target capabilities:

- Vehicles and assets
- Drivers
- Trackers
- SIMs
- Telematics provider integration
- Trips
- Fuel records
- Maintenance history
- Licence tracking
- Insurance tracking
- Tracker assignments
- Driver assignments
- Fleet profitability
- Vehicle 360 view

The Vehicle 360 view should show:

- GPS tracker
- Driver
- Fuel consumption
- Maintenance cost
- Parts used
- Insurance
- Licence status
- Costs
- Revenue generated
- Invoices
- Trips
- Profitability

### Accounting

Accounting is the v4 backbone.

MVP features:

- Dashboard
- Cash balance
- Receivables
- Payables
- Revenue
- Expenses
- Profit
- Taxes
- Chart of accounts
- Journal entries
- General ledger
- Trial balance
- Balance sheet
- Income statement
- Cash flow
- Bank accounts
- Bank reconciliation
- Petty cash
- Budgets
- Customer statements
- Receipts
- Credit notes
- Customer aging
- Supplier bills
- Supplier payments
- Outstanding payables

### Inventory

Inventory should work for warehouses, workshops, fleet parts, device stock, and retail-style stock.

Target features:

- Products
- Services
- Categories
- Units of measure
- Brands
- Serial numbers
- Batch numbers
- Multiple warehouses
- Bin locations
- Transfers
- Stock counts
- Adjustments
- Current stock
- Available stock
- Reserved stock
- Reorder levels

### Sales

Sales should connect directly with accounting.

Workflow:

```text
Quotation
-> Sales Order
-> Delivery Note
-> Invoice
-> Payment
```

Target features:

- Quotations
- Sales orders
- Delivery notes
- Invoices
- Credit notes
- Receipts
- Customer statements
- Customer aging

### Purchasing

Purchasing should connect suppliers, inventory, and accounting.

Workflow:

```text
Purchase Request
-> RFQ
-> Purchase Order
-> Goods Receipt
-> Supplier Invoice
-> Payment
```

Target features:

- Suppliers
- RFQs
- Purchase orders
- Goods received notes
- Supplier bills
- Supplier payments
- Outstanding payables

### Invoicing

Invoicing can exist as a lightweight entry point for small businesses while still posting into accounting.

Target features:

- Invoice templates
- PDF generation
- Email sending
- Payment tracking
- Partial payments
- VAT
- Discounts
- Credit notes
- Receipts

### CRM

CRM should feel like a real sales platform, not a contact list.

Workflow:

```text
Lead
-> Qualification
-> Opportunity
-> Quotation
-> Won
-> Customer
```

Target features:

- Leads
- Contacts
- Organizations
- Opportunities
- Pipeline
- Tasks
- Calendar
- Calls
- Emails
- Notes
- Customer 360 view

Customer 360 should show:

- Fleet
- Invoices
- Payments
- Vehicles
- Drivers
- Trackers
- Maintenance
- Fuel
- Trips
- Contracts
- Support tickets

### Maintenance

Maintenance ties fleet, inventory, technicians, invoicing, and accounting together.

Workflow:

```text
Vehicle
-> Service Due
-> Work Order
-> Technician Assigned
-> Parts Used
-> Invoice Generated
-> Accounting Updated
```

Target features:

- Service schedules
- Maintenance requests
- Work orders
- Technician assignment
- Parts consumption
- Maintenance history
- Billable repairs
- Internal repairs
- Cost tracking

### Asset Management

Asset management should cover company-owned and customer-managed assets.

Target features:

- Vehicles
- Laptops
- Generators
- UPS systems
- Tools
- Office equipment
- Depreciation schedules
- Service history
- Assignments
- Insurance
- Documents

### HR

Target features:

- Employees
- Departments
- Leave
- Payroll
- Attendance
- Performance
- Employee documents

### Projects

Useful for engineering and service companies.

Workflow:

```text
Project
-> Tasks
-> Budgets
-> Expenses
-> Invoices
```

Target features:

- Projects
- Tasks
- Budgets
- Expenses
- Timesheets
- Project invoices
- Profitability

### Documents

Document storage should be shared across the platform.

Target document types:

- Contracts
- Licences
- Insurance documents
- Vehicle registrations
- Tax certificates
- Purchase orders
- Invoices
- Supplier bills
- Maintenance records
- Compliance evidence

## Phased Delivery Plan

### Phase 0 - v4 Foundation

Goal: establish the platform base before adding broad ERP screens.

Deliverables:

- Rename product surface to Omni Business Platform
- Define company/tenant model
- Define party model
- Define item/product/service model
- Define document framework
- Define document numbering system
- Define accounting posting engine design
- Define module permission model
- Define stock movement model
- Define asset model direction
- Define UI navigation information architecture
- Decide migration path from hubs/customers/assets to v4 parties/assets
- Document API conventions for v4 modules

Success criteria:

- New modules can share parties, items, users, permissions, documents, and audit logs.
- The team can add accounting, inventory, sales, and purchasing without duplicating customer or product data.

### Phase 1 - MVP ERP

Goal: deliver the smallest usable ERP core.

Build first:

- Accounting
- Inventory
- Sales
- Purchasing
- Invoicing

Recommended order:

1. Shared parties, items, document numbering, tax, currency, fiscal settings
2. Chart of accounts and journal entries
3. General ledger and trial balance
4. Customers, suppliers, products, and services
5. Quotes, invoices, receipts, and credit notes
6. Supplier bills and supplier payments
7. Warehouses and stock movements
8. Purchase orders and goods received notes
9. Sales orders and delivery notes
10. Financial reports

Success criteria:

- A company can create customers and suppliers.
- A company can sell products or services.
- A company can invoice customers and record receipts.
- A company can buy from suppliers and record payments.
- Inventory movements are captured.
- Financial transactions post to the ledger.

### Phase 2 - CRM and Fleet Integration

Goal: connect the ERP base to the customer pipeline and fleet operations.

Deliverables:

- Leads
- Opportunities
- CRM pipeline
- CRM tasks and notes
- Customer 360
- Fleet 360
- Telematics asset sync design
- Vehicle profitability
- Customer fleet, invoices, payments, vehicles, drivers, trackers, maintenance, fuel, trips, contracts, and support tickets in one view

Success criteria:

- Sales teams can convert leads into customers and quotes.
- Fleet records connect to customer and accounting records.
- Customer records provide a complete operational and financial view.

### Phase 3 - Maintenance, Assets, HR, and Projects

Goal: deepen Omni's operational advantage.

Deliverables:

- Maintenance work orders
- Service schedules
- Parts consumption from inventory
- Technician workflow improvements
- Billable maintenance invoices
- Asset depreciation
- Asset service history
- Employees
- Leave
- Attendance
- Payroll foundation
- Projects
- Project tasks
- Project budgets
- Project expenses
- Project invoices

Success criteria:

- Maintenance connects fleet, inventory, technicians, invoicing, and accounting.
- Assets have financial and service histories.
- Projects can track work, expenses, budgets, and invoices.

### Phase 4 - Hardening, Automation, and Scale

Goal: make v4 reliable for real businesses.

Deliverables:

- Approval workflows
- Import/export
- Advanced reports
- Bank reconciliation automation
- Email templates
- PDF templates
- Background jobs
- Notifications
- Audit log coverage across all modules
- Backup and restore procedures
- Observability
- Regression test suites
- Role and permission testing
- Migration tooling from v3 data

Success criteria:

- The platform is safe to operate with real financial and operational data.
- Admins can understand who changed what and when.
- Reports reconcile with transactional data.

## Navigation Plan

The v4 UI should use product-area navigation rather than the current v3 internal operations grouping.

Recommended navigation:

```text
Dashboard

Operations
  Fleet
  Dispatch
  Maintenance
  Drivers

Sales
  CRM
  Quotations
  Orders
  Invoices

Purchasing
  Suppliers
  Purchase Orders
  Bills

Inventory
  Products
  Warehouses
  Stock

Finance
  Accounting
  Banking
  Reports

People
  Employees
  Customers
  Suppliers

Projects
  Projects
  Tasks
  Budgets
  Expenses

Administration
  Users
  Roles
  Settings
  Audit Trail
  Compliance
```

Navigation should be:

- Role-aware
- Company-configurable
- Module-aware
- Searchable
- Conservative by default

A small transport company should not be forced to see every advanced module on day one.

## UI Strategy

The v4 UI must feel like a serious business platform, not a decorative admin dashboard. It should be calm, fast, predictable, and easy to operate every day. The design goal is not to impress users with visual effects; it is to help them find work, complete transactions, understand risk, and move through business processes with confidence.

### UI Product Direction

The product surface should be renamed from **Omni Admin** to **Omni Business Platform**.

The admin-only feeling should be reduced. Users should feel they are entering a business operating system with role-based modules, not an internal control panel.

Recommended top-level shell:

```text
Omni Business Platform
|
+-- Global search / command bar
+-- Company switcher
+-- Module navigation
+-- Current workspace
+-- Notifications
+-- User menu
+-- Help / documentation
```

### Design Personality

The UI should feel:

- Simple
- Operational
- Trustworthy
- Fast
- Businesslike
- Structured
- Low-friction

The UI should avoid:

- Overly decorative cards
- Marketing-style hero layouts inside the app
- Too many gradients
- Oversized headings in work screens
- Repeating the same metric cards everywhere
- Hiding important actions inside unclear menus
- Showing advanced modules to users who do not need them

### App Shell

The app shell should use a persistent sidebar on desktop and a compact drawer on mobile.

Desktop shell:

```text
+--------------------------------------------------------------+
| Top bar: company, search, notifications, user                |
+----------------------+---------------------------------------+
| Sidebar              | Page header                           |
| Dashboard            | Filters / actions                     |
| Operations           | Main work area                        |
| Sales                |                                       |
| Purchasing           |                                       |
| Inventory            |                                       |
| Finance              |                                       |
| People               |                                       |
| Projects             |                                       |
| Administration       |                                       |
+----------------------+---------------------------------------+
```

The sidebar should show product areas first, then nested modules. It should support collapsing, but labels should remain visible by default because ERP users benefit from clarity more than minimalism.

The top bar should include:

- Company switcher
- Global search
- Quick create button
- Notifications
- Current user
- Help link

### Global Search and Quick Actions

Global search should become a first-class feature.

Users should be able to search:

- Customers
- Suppliers
- Vehicles
- Drivers
- Invoices
- Quotes
- Purchase orders
- Products
- Assets
- Work orders
- Employees
- Projects

Search results should show the record type, status, and key identifier.

Quick create should support common actions:

- New customer
- New quote
- New invoice
- New receipt
- New supplier bill
- New product
- New purchase order
- New vehicle
- New work order

### Dashboard Strategy

Dashboards should be practical and action-oriented.

Do not build dashboards as decorative KPI pages. Every dashboard card should either:

- Reveal risk
- Show workload
- Link to records needing action
- Summarize financial health
- Summarize operational health

Recommended main dashboard sections:

- Cash position
- Receivables due
- Payables due
- Sales pipeline
- Open invoices
- Low stock
- Vehicles needing attention
- Maintenance due
- Open work orders
- Recent activity

Avoid a dashboard filled only with totals such as "customers", "users", and "devices". Totals are useful, but they do not tell the user what to do next.

### Module Landing Pages

Each module should have a simple landing page with:

- Key action buttons
- Records needing attention
- Recent records
- Saved views
- A compact module summary

Example: Finance landing page

```text
Finance
|
+-- Cash balance
+-- Receivables due
+-- Payables due
+-- Unposted journals
+-- Bank reconciliation queue
+-- Recent invoices
+-- Recent payments
```

Example: Fleet landing page

```text
Fleet
|
+-- Vehicles active
+-- Vehicles needing maintenance
+-- Licence expiries
+-- Tracker issues
+-- Driver assignments
+-- Recent trips / telematics sync status
```

### Tables and Lists

Tables will be the heart of v4. They must be clean and efficient.

Every major list should support:

- Search
- Filters
- Saved views
- Sorting
- Pagination
- Bulk actions
- Export where appropriate
- Column visibility where useful
- Clear empty states

Table rows should include enough information to act without opening every record.

Example invoice table columns:

- Invoice number
- Customer
- Date
- Due date
- Status
- Total
- Paid
- Balance
- Actions

Example vehicle table columns:

- Registration / asset name
- Customer / hub
- Driver
- Tracker status
- Maintenance status
- Licence expiry
- Profitability indicator
- Actions

### Forms

Forms should be short, grouped, and forgiving.

Rules:

- Split long forms into sections or steps.
- Keep required fields obvious.
- Save drafts where workflows are long.
- Validate inline.
- Avoid asking for data before it is needed.
- Use sensible defaults.
- Keep destructive actions separate from save actions.
- Show computed totals immediately for financial documents.

Recommended form layout:

```text
Header
  Record title
  Status
  Primary action

Main form
  Essential details
  Lines / items
  Taxes / totals
  Notes
  Attachments

Side panel
  Customer/supplier summary
  Dates
  Owner
  Audit summary
```

### Record Detail Pages

Every important record should have a consistent detail layout.

Recommended layout:

```text
Record header
  Name / number
  Status
  Primary action
  Secondary actions

Summary strip
  Key financial, operational, or status facts

Tabs
  Overview
  Transactions
  Documents
  Activity
  Settings / Advanced
```

Every important record should answer:

- What is this?
- Who owns it?
- What status is it in?
- What changed recently?
- What money, stock, or asset does it affect?
- What is the next action?

### 360 Views

360 views are one of the most important v4 usability ideas.

The platform should include:

- Customer 360
- Vehicle 360
- Supplier 360
- Employee 360
- Project 360
- Asset 360

These views should combine operational, financial, document, and activity history in one place.

Customer 360 should show:

- Profile
- Contacts
- Quotes
- Orders
- Invoices
- Payments
- Vehicles
- Drivers
- Trackers
- Maintenance
- Fuel
- Trips
- Contracts
- Support tickets
- Documents
- Activity timeline

Vehicle 360 should show:

- Vehicle details
- Customer/operator
- Driver
- Tracker
- SIM
- Telematics provider status
- Trips
- Fuel
- Maintenance
- Parts used
- Insurance
- Licence documents
- Revenue
- Costs
- Profitability
- Activity timeline

### Workflow Clarity

Workflow status should be visible at the top of records.

Users should always know:

- Current status
- Previous step
- Next step
- Blocking issue, if any
- Who can approve or post the record

Primary actions should change based on status.

Example:

- Draft invoice: `Approve`
- Approved invoice: `Send`
- Sent invoice: `Record payment`
- Partially paid invoice: `Record payment`
- Paid invoice: no payment action, show `View receipt`

### Document Statuses

Sales invoice:

```text
Draft
-> Approved
-> Sent
-> Partially Paid
-> Paid / Overdue / Cancelled
```

Purchase order:

```text
Draft
-> Approved
-> Sent
-> Partially Received
-> Received
-> Billed
-> Paid
```

Maintenance job:

```text
Reported
-> Scheduled
-> In Progress
-> Parts Used
-> Completed
-> Invoiced
```

CRM opportunity:

```text
Lead
-> Qualified
-> Opportunity
-> Quoted
-> Won / Lost
-> Customer
```

### Mobile and Small Screens

Mobile should support review, approval, search, and light updates. Heavy accounting and inventory workflows can remain desktop-first, but they must still be readable on tablets.

Mobile priorities:

- Search records
- View customer/vehicle/invoice details
- Approve documents
- Upload attachments
- View work orders
- Update job status
- Capture photos or notes
- Contact customer or supplier

Avoid forcing dense financial tables into cramped mobile layouts. Use stacked record cards on small screens.

### Accessibility and Readability

The platform should be usable for long working sessions.

Rules:

- Strong contrast
- Legible font sizes
- Predictable focus states
- Keyboard-accessible controls
- Clear error messages
- No text overlapping controls
- No important information conveyed by color alone
- Compact but not cramped spacing
- Consistent status colors

### Visual System

Use a restrained business palette with semantic colors:

- Neutral background
- Clear primary action color
- Green for success/paid/active
- Amber for warning/due/attention
- Red for overdue/failed/critical
- Blue or cyan only where it supports brand or navigation

Avoid letting the UI become dominated by one hue. The app should not feel like a dark-blue or cyan-only dashboard.

Cards should be used for:

- Metrics
- Record summaries
- Repeated items
- Modals
- Focused tools

Cards should not be used to wrap every page section. Dense operational screens should use tables, split panes, tabs, and clear page sections.

### Module-Specific UI Recommendations

#### Accounting UI

Accounting screens should prioritize accuracy and auditability.

Recommended screens:

- Accounting dashboard
- Chart of accounts table
- Journal entry list
- Journal entry editor
- General ledger
- Trial balance
- Balance sheet
- Income statement
- Cash flow
- Bank reconciliation workspace

Accounting UI rules:

- Always show debit and credit totals.
- Prevent posting unbalanced journals.
- Separate draft and posted records clearly.
- Make reversal/correction workflows explicit.
- Do not allow silent edits to posted entries.

#### Inventory UI

Inventory screens should prioritize speed and stock clarity.

Recommended screens:

- Product list
- Product detail
- Warehouse list, limited to real Omni stock branches by default
- Stock on hand
- Stock movements
- Stock adjustment
- Transfer workflow
- Stock count workflow

Inventory UI rules:

- Show current, available, reserved, and reorder quantities.
- Make warehouse and bin location visible.
- Make serial/batch numbers easy to scan.
- Use barcode/serial-friendly input patterns where possible.

#### Sales UI

Sales screens should make document flow obvious.

Recommended screens:

- CRM pipeline
- Quote list
- Quote editor
- Sales order list
- Invoice list
- Invoice editor
- Receipt capture
- Customer statement

Sales UI rules:

- Show document totals clearly.
- Keep customer balance visible.
- Make quote-to-order-to-invoice conversion one action where possible.
- Show payment status everywhere invoices appear.

#### Purchasing UI

Purchasing screens should focus on approval, receipt, and supplier obligations.

Recommended screens:

- Supplier list
- RFQ list
- Purchase order list
- Goods receipt workspace
- Supplier bill list
- Payables aging

Purchasing UI rules:

- Show ordered, received, billed, and paid quantities/amounts.
- Make partial receipts easy to record.
- Keep supplier balance visible.

#### Fleet and Maintenance UI

Fleet screens should emphasize operational condition and profitability.

Recommended screens:

- Fleet dashboard
- Vehicle list
- Vehicle 360
- Driver list
- Tracker/SIM assignment
- Maintenance schedule
- Work order board
- Fuel records
- Licence and insurance expiry board

Fleet UI rules:

- Show next maintenance due.
- Show licence/insurance expiry warnings.
- Show tracker/SIM health.
- Show vehicle profitability where financial data exists.
- Keep telematics provider integration status visible but not overwhelming.

#### CRM UI

CRM should feel like a sales workspace, not a static contacts table.

Recommended screens:

- Lead inbox
- Pipeline board
- Opportunity detail
- Activity tasks
- Customer 360
- Contacts and organizations

CRM UI rules:

- Make next follow-up obvious.
- Show deal stage, value, probability, and owner.
- Allow quick notes, calls, and tasks.

### UI Success Criteria

The v4 UI is successful when:

- A new user can understand the sidebar without training.
- A returning user can reach common records in seconds.
- Each module has a clear main workflow.
- Users can tell what needs attention from the dashboard.
- Users can complete common tasks without opening many browser tabs.
- Financial documents clearly show draft, approved, posted, paid, and cancelled states.
- Fleet records connect naturally to invoices, maintenance, trackers, drivers, and documents.
- The app remains usable on a laptop during a full workday.
- Mobile supports field and approval workflows without pretending to replace desktop accounting.

## Migration Strategy

The v3 system should become the operational foundation for v4, not be thrown away.

Recommended mapping:

- Current hubs become customer operating accounts or fleet groups.
- Current users remain identity records.
- Current hub memberships become customer/user/role relationships.
- Current vehicles become assets.
- Current hardware inventory becomes serialized inventory items and fleet tracker records.
- Current SIM inventory becomes serialized inventory or connectivity assets.
- Current technician jobs become maintenance/field service work orders.
- Current enquiries become CRM leads or opportunities.
- Current subscriptions become recurring billing agreements or service contracts.
- Current billing fields become inputs to proper invoicing and accounting.
- Current compliance registers remain under governance/administration.
- Current audit log becomes the base for platform-wide audit logging.

Warehouse decision:

- Warehouses represent physical places where Omni-owned hardware or SIM stock is kept.
- The initial live warehouses are `Kwekwe Warehouse` and `Hwange Warehouse`.
- Do not create customer-specific warehouses for hubs. Customer assignment belongs on tracker/SIM assignment, installation, vehicle, and contract records.

## Omni Operations Lifecycle

This is the working lifecycle the admin UI should make obvious:

1. Inventory receives tracker hardware and SIM cards into real Omni warehouses.
2. A tracker and SIM may be pre-paired as a prepared kit before any customer is known.
3. A public enquiry or internal sale creates an Omni Onboarding Job, with a Lead linked for sales traceability where available.
4. The onboarding job first creates or reuses the customer hub.
5. The onboarding job creates or reuses the customer fleet profile.
6. The onboarding job captures the vehicles that need tracking.
7. A prepared kit is reserved or assigned to a customer hub and vehicle.
8. Installation is scheduled, started, completed or marked failed/cancelled.
9. Completion updates the tracker and SIM inventory state to Installed and links them to the customer vehicle.
10. The telematics unit link connects the installed vehicle to the external provider.
11. The customer portal exposes the vehicle, documents, invoices, tickets and tracking handoff for that customer only.
12. Quotation, invoicing, support, maintenance and account management continue from the customer fleet profile and vehicle record.

UI rule:

- Every operational form should show the current lifecycle position, the next practical action, and direct links to the related records a user needs next.

Customer portal user rule:

- Role Profiles are for internal Omni users only.
- Customer portal users should be Frappe `Website User` accounts with the `Customer Portal User` role.
- A customer portal user must be linked to the relevant hub/customer through the ERPNext Customer `portal_users` child table and a Contact record where contact details are available.
- Staff should create customer portal users from `Omni Onboarding Job` during onboarding or from `Customer Fleet Profile` for an existing customer.

## Non-Goals for Early v4

To keep the project successful, early v4 should avoid:

- Building every ERP module at once
- Replacing the whole v3 UI before the data model is ready
- Building payroll before accounting is stable
- Building project accounting before basic invoicing and expenses are stable
- Adding complex telematics automation before the internal asset/customer/accounting model is clean
- Creating separate customer, supplier, CRM organization, and accounting debtor tables that duplicate the same real-world entity
- Posting accounting balances directly from UI forms without a controlled posting engine
- Treating dashboards as a substitute for transaction workflows

## First Implementation Milestones

### Milestone 1 - v4 Blueprint

- Create v4 architecture docs
- Finalize module boundaries
- Finalize shared data model
- Finalize navigation map
- Decide naming conventions
- Decide migration rules from v3 models

### Milestone 2 - Shared Platform Primitives

- Company/tenant model
- Party model
- Item model
- Document numbering
- Module permissions
- Extended audit log

### Milestone 3 - Accounting Core

- Chart of accounts
- Journal entries
- General ledger
- Trial balance
- Fiscal periods
- Tax rates
- Bank/cash accounts

### Milestone 4 - Sales and Invoicing MVP

- Customers
- Products/services
- Quotations
- Invoices
- Receipts
- Credit notes
- PDF generation
- Email sending

### Milestone 5 - Purchasing and Inventory MVP

- Suppliers
- Purchase orders
- Goods received notes
- Supplier bills
- Supplier payments
- Warehouses
- Stock movements
- Stock adjustments

### Milestone 6 - Fleet Integration

- Convert v3 hubs/assets into v4 party/asset model
- Link vehicles/assets to customers
- Link tracker/SIM inventory to stock and assets
- Link technician jobs to maintenance work orders
- Add vehicle profitability foundation

## Implementation Log

### 2026-07-08 - Phase 0 Started

Initial implementation began with additive v4 foundations rather than a disruptive replacement of v3 workflows.

Completed first slice:

- Added Omni v4 foundation SQLAlchemy models.
- Added an additive migration for `v4_*` platform tables.
- Added a regression test for the shared business graph.
- Started UI repositioning by renaming the admin shell surface to **Omni Business Platform**.

Foundation tables introduced:

- `v4_companies`
- `v4_parties`
- `v4_items`
- `v4_document_sequences`
- `v4_fiscal_periods`
- `v4_accounts`
- `v4_documents`
- `v4_document_lines`
- `v4_journal_entries`
- `v4_journal_lines`
- `v4_warehouses`
- `v4_stock_movements`

This first slice intentionally does not remove or rename existing v3 tables. Current hubs, users, assets, tracker inventory, SIM inventory, technician jobs, subscriptions, compliance records, and audit logs remain operational while v4 primitives are introduced alongside them.

## Definition of Success

Omni v4 is successful when:

- Fleet remains the flagship feature.
- Accounting becomes the financial backbone.
- Inventory becomes the operational stock layer.
- Sales and purchasing create real accounting documents.
- Customers, suppliers, employees, and contacts are shared through one party model.
- Products, services, fleet parts, and billable items are shared through one item model.
- Users can understand the next action on every important record.
- Small businesses can start with simple workflows.
- Larger businesses can grow into deeper modules without data being re-entered.
- The platform feels integrated rather than bolted together.
