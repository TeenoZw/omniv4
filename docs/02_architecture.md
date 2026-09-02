# 02 - Omni v4 Current Architecture

## Purpose

This document describes the current Omni v4 architecture.

Older Omni v3 documentation described a FastAPI/PostgreSQL backend with separate Svelte admin and customer apps. That code remains useful for migration and reference, but it is not the active v4 architecture.

## Architecture Summary

```text
                         Omni v4

┌─────────────────────────────────────────────────────────────┐
│ Public Website                                               │
│ www.omnilogistics.co.zw                                      │
│ Svelte / client-web                                          │
│                                                             │
│ Brand, services, lead capture, portal entry point            │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Customer Portal                                              │
│ www.omnilogistics.co.zw/portal or portal.omnilogistics.co.zw │
│ Svelte / client-web                                          │
│                                                             │
│ Vehicles, tracker status, documents, invoices, support       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                         Narrow Omni APIs
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Admin / Business Engine                                      │
│ admin.omnilogistics.co.zw                                    │
│ Frappe + ERPNext + omni_operations                           │
│                                                             │
│ Accounting, customers, fleet, trackers, maintenance,         │
│ inventory, invoices, permissions, fiscalisation, reporting   │
└──────────────────────────────┬──────────────────────────────┘
                               │
          ┌────────────────────┴────────────────────┐
          ▼                                         ▼
┌───────────────────────┐                 ┌───────────────────────┐
│ Telematics Providers  │                 │ External Compliance    │
│ Wialon first adapter  │                 │ ZIMRA FDMS path        │
│ Provider-neutral core │                 │ Fiscalisation          │
└───────────────────────┘                 └───────────────────────┘
```

## Main Components

### Frappe / ERPNext

Location:

```text
erpnext-eval/frappe_docker/development/frappe-bench
```

Role:

- Internal admin application
- ERP/accounting backbone
- Permission engine
- Workflow engine
- Reporting base
- Background jobs and scheduled syncs

ERPNext should own:

- Company setup
- Customers
- Suppliers
- Items
- Warehouses
- Sales invoices
- Purchase invoices
- Payments
- Accounting reports
- Stock and inventory records where practical

### Omni Operations

Location:

```text
erpnext-eval/frappe_docker/development/frappe-bench/apps/omni_operations
```

Role:

- Custom Frappe app for Omni-specific operations.

Omni Operations owns:

- Fleet vehicles
- Drivers
- Tracker profiles
- SIM profiles
- Tracker SIM assignments
- Tracker installations
- Telematics provider accounts
- Telematics unit links
- Telematics sync logs
- Customer fleet views
- Fleet contracts
- Maintenance workflows
- ZIMRA/fiscalisation support structures
- Omni workspaces, roles, and operational reports

Design rule:

Omni Operations extends ERPNext. It should not duplicate ERPNext accounting, customer, invoice, payment, or stock concepts without a deliberate reason.

### Svelte Public Website and Customer Portal

Location:

```text
client-web
```

Role:

- Public Omni Logistics website
- Customer-facing Omni portal

The Svelte portal should call narrow Frappe/Omni APIs such as:

- current portal user/customer
- customer dashboard summary
- vehicles
- vehicle detail
- tracker status
- invoices and payment status
- documents
- support tickets

The customer portal should not expose generic ERPNext Desk routes.

### Legacy v3 Code

Locations:

```text
backend
admin-web
```

Status:

- Legacy reference and migration source.

The v3 code is still useful for:

- understanding previous data behavior
- comparing UI patterns
- migration mapping
- validating historical customer/hub/vehicle semantics

It should not be treated as the active v4 backend or admin application.

## Data Ownership

| Data area | System of record |
| --- | --- |
| Customers and hubs | ERPNext Customer plus Omni hub/company mapping |
| Vehicles | Omni Operations |
| Trackers and SIMs | Omni Operations |
| Tracker/SIM pairing lifecycle | Tracker SIM Assignment in Omni Operations |
| Telematics provider credentials | Omni Operations, stored securely in Frappe/site secrets |
| Invoices and payments | ERPNext |
| Items and warehouses | ERPNext |
| Maintenance work | Omni Operations with ERPNext links where billing/stock is involved |
| Fiscalisation records | Omni Operations linked to ERPNext invoices |
| Customer portal users | Frappe users with Omni customer scoping |

## Domain Responsibilities

| Domain | Responsibility |
| --- | --- |
| `www.omnilogistics.co.zw` | Public Svelte site |
| `www.omnilogistics.co.zw/portal` | Preferred Svelte customer portal path |
| `portal.omnilogistics.co.zw` | Optional dedicated customer portal host |
| `admin.omnilogistics.co.zw` | Frappe/ERPNext admin app |

## Integration Boundaries

### Tracker and SIM Assignment

SIM assignment is modelled as a relationship, not as a single permanent field on a tracker.

The source of truth is:

- Tracker SIM Assignment

This supports:

- pre-pairing a SIM with tracker hardware before customer onboarding
- one active SIM per tracker slot
- future dual-SIM trackers through `Primary` and `Secondary` slots
- one active tracker assignment per SIM
- customer/vehicle assignment only when the kit becomes operational

Lifecycle:

- `Available`: tracker or SIM is in stock and unused.
- `Prepared`: SIM is paired with tracker hardware, but no customer or vehicle is required yet.
- `Reserved`: kit is held for a customer/job.
- `Assigned`: kit is assigned to a customer and vehicle/job.
- `Installed`: kit is installed on a customer vehicle.
- `Removed` / `Cancelled`: assignment is no longer active.

### Telematics

The core model must remain provider-neutral:

- Telematics Provider
- Telematics Provider Account
- Telematics Unit Link
- Telematics Sync Log

Wialon is the first real provider adapter. A future provider should require a new adapter, not a redesign of vehicles or customer ownership.

### ZIMRA Fiscalisation

ZIMRA integration should be implemented as an auditable fiscalisation service around ERPNext invoices.

Invoices should remain usable while fiscalisation is pending, failed, or retrying, but their fiscalisation status must be visible and traceable.

### Customer Portal API

The portal API layer must enforce customer scoping server-side.

Client-side filtering is not security.

## Development Priorities

1. Keep the repo documentation aligned with this architecture.
2. Build the narrow Frappe portal API layer.
3. Wire the Svelte portal to the Frappe APIs.
4. Keep the Frappe admin workspace Omni-focused.
5. Rehearse migration from a fresh v3 Supabase export.
6. Validate real telematics sync.
7. Complete ZIMRA onboarding and live fiscalisation implementation.
8. Harden production deployment, backups, monitoring, roles, and secrets.
