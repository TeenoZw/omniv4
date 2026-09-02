# 16 - Operational Workflow & Role Matrix

This document defines the **current Omni Operations workflow** for v4. Omni manages enquiries, onboarding, inventory, installation, billing, support, documents, maintenance, and customer portal access. Telematics providers such as Wialon provide tracking data through provider-neutral links.

## Overview

- **Scope:** Enquiry intake, customer/hub onboarding, hardware/SIM stock, kit preparation, installation, billing, support, and customer portal access.
- **Primary Modules:** Frappe/ERPNext admin app, Omni Operations app, Svelte public site, Svelte customer portal.
- **Out of Scope (for now):** Partner portal, advanced route optimisation, and deep trip analytics.

## Role Taxonomy

- **Omni Users:** Directors, Operations Admin, Fleet Manager, Installation Coordinator, Technician, and future finance/support users. They work from the Omni Operations workspace.
- **Customer Portal Users:** Client-side users with `Customer Portal User` access. They are Website Users linked to a Customer/hub, not internal Role Profile users.

## Admin Workspace Rule

The first admin screen should stay simple:

1. New Client Onboarding
2. Prepare Tracker/SIM Kit
3. Installation Queue
4. Customer Fleets
5. Invoices
6. Support Queue

Everything else should sit under grouped work areas so users are not forced to understand every DocType before doing daily work.

## Lifecycle

```text
Stock trackers/SIMs
-> Onboard customer hub
-> Create customer fleet profile
-> Capture vehicles
-> Prepare/reserve tracker/SIM kit
-> Schedule installation
-> Complete installation
-> Link telematics
-> Invoice, support, documents and maintenance
```

## Stage 1: Enquiry and Onboarding

| Step | Action | Owner | System Touchpoints |
| --- | --- | --- | --- |
| 1.1 | Prospect submits enquiry or admin captures the client/hub details | Customer / Operations Admin | Public site, Lead, Omni Onboarding Job |
| 1.2 | Admin creates or opens `Omni Onboarding Job` | Operations Admin | New Client Onboarding |
| 1.3 | Guided setup creates/reuses the Customer hub | Operations Admin | Customer |
| 1.4 | Guided setup creates/reuses the Customer Fleet Profile | Operations Admin | Customer Fleet Profile |
| 1.5 | Admin captures the vehicles that need tracking | Operations Admin / Fleet Manager | Fleet Vehicle |
| 1.6 | Admin qualifies or links the lead and prepares quotation when needed | Operations Admin / Director | Lead, Opportunity, Quotation |
| 1.7 | Admin provisions customer portal user after the operational record exists | Operations Admin | Website User + Customer Portal User |

## Stage 2: Inventory and Kit Preparation

| Step | Action | Owner | System Touchpoints |
| --- | --- | --- | --- |
| 2.1 | Receive trackers and SIMs into physical warehouse | Operations Admin / Inventory user | Kwekwe Warehouse, Hwange Warehouse |
| 2.2 | Create tracker and SIM profiles | Operations Admin | Tracker Profile, SIM Profile |
| 2.3 | Pair tracker and SIM as `Prepared` kit when useful | Technician / Coordinator | Tracker SIM Assignment |
| 2.4 | Reserve kit for a customer once onboarding starts | Coordinator | Tracker SIM Assignment |
| 2.5 | Assign kit to customer vehicle before installation | Coordinator / Technician | Tracker SIM Assignment |

## Stage 3: Installation

| Step | Action | Owner | System Touchpoints |
| --- | --- | --- | --- |
| 3.1 | Schedule installation against the customer vehicle | Installation Coordinator | Tracker Installation |
| 3.2 | Technician starts work | Technician | Tracker Installation: In Progress |
| 3.3 | Technician completes work and captures signoff | Technician | Tracker Installation: Completed |
| 3.4 | System updates tracker/SIM assignment state | System | Tracker SIM Assignment, Tracker Profile, SIM Profile |

## Stage 4: Telematics Handoff

| Step | Action | Owner | System Touchpoints |
| --- | --- | --- | --- |
| 4.1 | Link provider unit to Omni vehicle | Operations Admin | Telematics Unit Link |
| 4.2 | Sync provider data | Operations Admin / System | Telematics Provider Account |
| 4.3 | Confirm portal visibility for the right customer | Operations Admin | Customer Portal |

## Stage 5: Billing and Customer Care

| Step | Action | Owner | System Touchpoints |
| --- | --- | --- | --- |
| 5.1 | Create contract or billing agreement | Operations Admin / Finance | Fleet Contract |
| 5.2 | Convert quotation/order to invoice | Finance | Sales Invoice |
| 5.3 | Generate invoice PDF and send to customer | Finance | ERPNext print/email |
| 5.4 | Record payment | Finance | Payment Entry |
| 5.5 | Handle customer support, documents and maintenance | Operations Admin / Technician | Issue, Fleet Document, Maintenance Work Order |

## Implementation Notes

- Keep hubs as ERPNext Customers, not ERPNext Companies.
- Use `Omni Industrial Solutions` as the accounting Company unless a real legal entity is added.
- Warehouses represent physical Omni stock branches only: `Kwekwe Warehouse` and `Hwange Warehouse`.
- New onboarding must start with the operational prerequisites: Customer/hub, Customer Fleet Profile, Fleet Vehicle, tracker/SIM kit, and Tracker Installation. Lead, quotation, portal access, and billing follow once the core client and asset records are in place.
- Every key form should show current lifecycle stage, next practical action, and direct links/buttons for where to go next.

**Last Updated:** 2026-09-01
