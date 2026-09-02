# 40 - Omni v4 Consolidation Execution Plan

## Purpose

This plan turns the professional clean-pass recommendations into an execution path for making Omni v4 a coherent company-grade platform.

The goal is to stop running multiple competing product architectures and consolidate around one clear direction:

- Frappe/ERPNext is the internal business and operations engine.
- Svelte is the public website and customer-facing portal experience.
- The old v3 FastAPI/backend/admin code is retained only as migration/reference material unless explicitly revived.
- Omni-specific workflows sit on top of ERPNext instead of replacing ERPNext accounting, customers, invoices, stock, and permissions.

## Guiding Decisions

1. Omni v4 is not a generic ERP clone.
   It is an operations-first business platform with fleet, telematics, maintenance, customer service, billing, and fiscalisation at its core.

2. ERPNext should be the transaction backbone.
   Accounting, customers, suppliers, invoices, payments, items, warehouses, roles, and reports should use ERPNext wherever practical.

3. Frappe Desk is the admin application.
   Directors and internal staff use the Omni-focused Frappe workspace instead of a second custom admin app.

4. Svelte owns the public and customer experience.
   The public website and customer portal should feel like Omni products, not like ERPNext Desk pages.

5. The customer portal must use narrow Omni APIs.
   Portal users should not depend on broad Desk routes or generic ERPNext screens.

6. Telematics must remain provider-neutral.
   Wialon is the first adapter, not the permanent core model.

7. Production architecture must be defined before deeper polish.
   UI, auth, APIs, redirects, and deployment should all target the same domain strategy.

8. Partner expansion should be designed into the platform, but not allowed to distract the core MVP.
   Omni should support future certified installers, sales partners, Gold Partners, and regional partners through clean data models, permissions, onboarding, installation evidence, and commission records. The full partner portal comes after the internal onboarding, installation, customer portal, and work queue workflows are reliable.

## Target Architecture

### Public Website

Host:

- `www.omnilogistics.co.zw`

Runtime:

- Svelte app from `client-web`

Responsibilities:

- Public landing pages
- Omni Logistics brand presentation
- Product/service explanation
- Lead/contact entry points
- Customer portal entry point

### Customer Portal

Host:

- Preferred: `www.omnilogistics.co.zw/portal`
- Acceptable alternative: `portal.omnilogistics.co.zw`

Runtime:

- Svelte app from `client-web`

Responsibilities:

- Customer dashboard
- Vehicles
- Tracker/telematics status
- Maintenance visibility
- Contracts/documents
- Invoices/payments
- Support tickets

API dependency:

- Narrow Frappe/Omni portal API endpoints

### Partner Portal

Host:

- Future preferred: `partners.omnilogistics.co.zw`

Runtime:

- Svelte partner-facing surface, backed by narrow Frappe/Omni partner APIs

Responsibilities:

- Partner onboarding
- Assigned installation jobs
- New installation submissions
- Tracker IMEI and SIM ICCID capture
- Installation checklist and photo evidence
- Activation approval status
- Partner stock visibility
- Support and warranty history
- Partner commission visibility

Initial rule:

Do not expose Wialon/provider administration or broad ERPNext Desk access to ordinary partners. Partners should work through Omni-specific workflows with least-privilege access.

### Admin Application

Host:

- `admin.omnilogistics.co.zw`

Runtime:

- Frappe/ERPNext bench with `omni_operations`

Responsibilities:

- Directors dashboard
- Fleet management
- Customer and hub management
- Vehicle and tracker operations
- Installation coordination
- Maintenance
- Accounting and billing
- Inventory
- ZIMRA/fiscalisation
- Permissions and administration

### Legacy v3 Code

Paths:

- `backend`
- `admin-web`
- old v3-specific docs

Status:

- Reference and migration source only

Rule:

- Do not add new v4 product features to legacy v3 areas unless the architecture is deliberately changed.

## Execution Phases

## Current Workflow Sprint - Finish the Core Operating Loop First

Objective:

Before building the regional partner network features, finish the internal Omni workflows that every later partner, customer, and country rollout will depend on.

Tasks:

| ID | Task | Output | Acceptance |
| --- | --- | --- | --- |
| W1-001 | Build `Omni Onboarding Job` | Frappe DocType/workflow | Done. One record coordinates a prospect/customer from enquiry through customer setup, vehicle setup, installation, portal access, and first invoice readiness. |
| W1-002 | Route public website enquiries into Frappe | Public enquiry API + Lead + Onboarding Job | A website enquiry creates or links an ERPNext Lead and opens an `Omni Onboarding Job` without using old v3 FastAPI assumptions. |
| W1-003 | Add guided installation actions and checklists | Tracker Installation workflow/actions | Coordinators and technicians can move installations through scheduled, in-progress, completed, failed, and rework states with required evidence. |
| W1-004 | Polish customer portal vehicle detail and ticket flows | Svelte portal routes/components | Customers can inspect a vehicle, telematics, documents, maintenance, invoices, and support history without needing Desk. |
| W1-005 | Add operations dashboards and work queues | Frappe dashboard/reports/workspace links | Directors, Operations Admin, Installation Coordinator, Fleet Manager, and Technician each see the work that matters to their role. |

Sequencing:

1. Start with `Omni Onboarding Job`, because it becomes the control record for public enquiries, customer setup, installations, and portal provisioning.
2. Add the public enquiry route next, because it feeds onboarding.
3. Improve installation checklists after onboarding exists, because onboarding needs to spawn and track installation work.
4. Polish the customer portal after vehicle/install data is better structured.
5. Build role dashboards and queues last in this sprint, because they should reflect the real records and statuses created by the first four tasks.

Professional note:

The partner expansion strategy depends on this sprint. A partner portal without reliable onboarding, installation, customer portal, and work queues would only expose unfinished internal process to outside users.

## Phase 1 - Consolidate the Project Truth

Objective:

Make the repo tell one clear story so future development does not drift.

Tasks:

| ID | Task | Output | Acceptance |
| --- | --- | --- | --- |
| C1-001 | Rewrite root README for Omni v4 | `README.md` | README clearly states active v4 architecture and marks v3 code as legacy/reference. |
| C1-002 | Add architecture summary | `docs/41_omniv4_current_architecture.md` or update `docs/02_architecture.md` | Architecture doc matches the target Frappe + Svelte direction. |
| C1-003 | Mark stale docs as legacy | Existing docs | Old FastAPI-only docs are clearly labelled as v3 legacy. |
| C1-004 | Add developer command map | README or `docs/42_omniv4_developer_runbook.md` | A developer can start admin, public site, portal, smoke checks, and client checks without guessing. |
| C1-005 | Define active/deprecated folders | README | `omni_operations` and `client-web` are active; `backend` and `admin-web` are reference unless revived. |

Professional note:

This comes first because confused documentation creates confused implementation.

## Phase 2 - Finalize Deployment Shape

Objective:

Make local development match the intended production split.

Tasks:

| ID | Task | Output | Acceptance |
| --- | --- | --- | --- |
| C2-001 | Confirm domain routing strategy | Deployment doc | Public, portal, admin, and API hostnames are documented. |
| C2-002 | Keep Frappe public route as fallback only | Frappe website routes | Visiting the admin host sends staff to Desk; public site is not primarily served by Frappe. |
| C2-003 | Document reverse proxy rules | Deployment doc | `www`, `portal`, and `admin` routing can be reproduced. |
| C2-004 | Decide API host/session approach | API architecture note | Svelte portal auth strategy is clear before endpoint work expands. |
| C2-005 | Add environment variable contract | `.env.example` and docs | Required public/portal/admin/API environment values are listed. |

Recommended default:

- `www.omnilogistics.co.zw` serves the Svelte public site.
- `www.omnilogistics.co.zw/portal` serves the Svelte customer portal.
- `admin.omnilogistics.co.zw` serves Frappe Desk.
- Frappe portal APIs are exposed through a controlled API path with strict auth and CORS/session rules.

## Phase 3 - Build the Frappe Portal API Layer

Objective:

Give the Svelte customer portal a clean, stable backend contract.

Tasks:

| ID | Task | Output | Acceptance |
| --- | --- | --- | --- |
| C3-001 | Define portal API contract | API doc | Endpoints, request shape, response shape, auth, and errors are documented. |
| C3-002 | Implement current customer endpoint | Frappe API | Portal can identify the logged-in user and their customer/hub scope. |
| C3-003 | Implement portal dashboard summary | Frappe API | Customer receives vehicle, invoice, support, and tracker status summary. |
| C3-004 | Implement vehicle list/detail API | Frappe API | Customer only sees vehicles linked to their customer/hub. |
| C3-005 | Implement telematics status API | Frappe API | Latest known tracker state can be displayed without exposing provider credentials. |
| C3-006 | Implement invoice/payment API | Frappe API | Customer sees their own invoices, balances, and payment status. |
| C3-007 | Implement document API | Frappe API | Customer sees contracts, certificates, and relevant uploaded documents only. |
| C3-008 | Expand support ticket API | Frappe API | Customer can create and view their own support requests. |
| C3-009 | Add portal permission tests | Frappe tests | Cross-customer data access is blocked and tested. |

API principle:

The Svelte portal should call Omni-specific endpoints, not generic ERPNext Desk routes.

## Phase 4 - Wire and Polish the Svelte Customer Portal

Objective:

Turn the customer portal from a branded shell into a useful customer product.

Tasks:

| ID | Task | Output | Acceptance |
| --- | --- | --- | --- |
| C4-001 | Replace old v3 API assumptions | `client-web` API layer | Portal no longer points to obsolete FastAPI-only routes. |
| C4-002 | Add authenticated portal dashboard | Svelte route | Customer lands on useful operational summary after login. |
| C4-003 | Add vehicles view | Svelte route/component | Vehicles are searchable, readable, and mobile-friendly. |
| C4-004 | Add vehicle detail view | Svelte route/component | Customer can see tracker, documents, maintenance, and support context. |
| C4-005 | Add invoices view | Svelte route/component | Customer can inspect invoice/payment status without ERPNext complexity. |
| C4-006 | Add documents view | Svelte route/component | Important fleet/customer documents are easy to find. |
| C4-007 | Add support view | Svelte route/component | Customer can submit and review tickets. |
| C4-008 | Add empty/error/loading states | Svelte components | The portal behaves gracefully when data is missing or APIs fail. |
| C4-009 | Run responsive UI pass | Screenshots/checks | Portal is usable on mobile, tablet, and desktop. |

UI principle:

The portal should optimize for what customers repeatedly check: vehicles, trackers, invoices, documents, maintenance, and support.

## Phase 5 - Focus the Frappe Admin Experience

Objective:

Make Desk feel like Omni operations, not a maze of ERPNext modules.

Tasks:

| ID | Task | Output | Acceptance |
| --- | --- | --- | --- |
| C5-001 | Clean Omni workspace navigation | Frappe workspace | Administrator sees Omni-first sections without hunting. |
| C5-002 | Add director dashboard priorities | Frappe dashboard/cards | Directors can quickly see fleet, revenue, support, installations, and fiscalisation status. |
| C5-003 | Add operations work queue | Frappe views/reports | Staff can act on installs, issues, tracker gaps, and maintenance. |
| C5-004 | Add customer 360 entry point | Frappe workspace/report | Staff can move from customer to vehicles, invoices, trackers, contracts, and support. |
| C5-005 | Add vehicle 360 entry point | Frappe workspace/report | Staff can see ownership, tracker, maintenance, documents, and billing context. |
| C5-006 | Hide or de-emphasize irrelevant modules | Role/workspace settings | ERPNext complexity is available when needed but not the first experience. |

Admin principle:

Use ERPNext power, but present Omni workflows first.

## Phase 6 - Migration Rehearsal and Data Cleanup

Objective:

Prove that v3 data can move into v4 cleanly and repeatably.

Tasks:

| ID | Task | Output | Acceptance |
| --- | --- | --- | --- |
| C6-001 | Take fresh Supabase export | Migration export files | Export is complete and dated. |
| C6-002 | Run import into clean Frappe site | Migration run | Import succeeds without relying on previous local state. |
| C6-003 | Produce reconciliation report | Migration report | Source counts and target counts are compared. |
| C6-004 | Validate hub-to-company/customer mapping | Migration report/data | Hubs are consistently represented as customer/company structures. |
| C6-005 | Validate vehicle ownership | Migration report/data | Each real vehicle belongs to the correct hub/customer. |
| C6-006 | Remove sample/test records | Clean site | Production candidate site has no accidental demo data. |
| C6-007 | Freeze migration mapping | Migration docs | Final mappings are documented for cutover. |

Migration principle:

No production cutover until migration can be repeated from a clean export with predictable results.

## Phase 7 - Telematics Production Validation

Objective:

Validate the provider-neutral telematics model using the real Wialon setup without locking Omni to Wialon forever.

Tasks:

| ID | Task | Output | Acceptance |
| --- | --- | --- | --- |
| C7-001 | Confirm master/provider account setup | Telematics Provider Account | One master account can sync customer hubs where permissions allow. |
| C7-002 | Sync real units | Unit links | Real external units match Omni vehicles without duplicates. |
| C7-003 | Verify hub/company ownership | Vehicle/customer links | Vehicles inherit the correct hub/company relationship. |
| C7-004 | Validate latest status polling | Sync logs/data | Coordinates, speed, and timestamp update for linked vehicles. |
| C7-005 | Validate portal scoping | Portal/API tests | Customers only see their own vehicles and tracker data. |
| C7-006 | Document provider adapter contract | Telematics docs | Future providers can be added without changing fleet core models. |

Telematics principle:

Wialon should be an adapter. Omni owns the operational model.

## Phase 8 - ZIMRA / Fiscalisation Readiness

Objective:

Move from fiscalisation skeleton to a certifiable production path once ZIMRA/device details are available.

Tasks:

| ID | Task | Output | Acceptance |
| --- | --- | --- | --- |
| C8-001 | Confirm legal/device onboarding path | ZIMRA notes | Company knows whether a device, certificate, or integrator process is required. |
| C8-002 | Store credentials/certificates securely | Site config/secrets | No sensitive material is committed to source. |
| C8-003 | Implement live FDMS provider | Frappe adapter | API methods support mTLS and official request/response shapes. |
| C8-004 | Add invoice fiscalisation queue | Frappe workflow | Invoices can be submitted, retried, and audited. |
| C8-005 | Add visible fiscalisation status | Desk/customer docs | Staff can tell whether an invoice is pending, submitted, failed, or retryable. |
| C8-006 | Test credit notes/offline recovery | Tests/manual QA | Failure and reversal scenarios are documented and handled. |

Fiscalisation principle:

Accounting documents should remain usable, but fiscal status must be explicit and auditable.

## Phase 9 - Production Hardening

Objective:

Prepare Omni v4 for real company use.

Tasks:

| ID | Task | Output | Acceptance |
| --- | --- | --- | --- |
| C9-001 | Pin production runtime versions | Deployment files/docs | MariaDB, Redis, Python, Node, Frappe, ERPNext versions are fixed. |
| C9-002 | Configure secrets strategy | Deployment docs | Tokens, passwords, certificates, and API keys are not stored in source. |
| C9-003 | Add backup and restore process | Runbook | Automated backups exist and restore has been tested. |
| C9-004 | Configure email and file storage | Production settings | Invoices, tickets, portal emails, and uploads work reliably. |
| C9-005 | Add monitoring/logging/error alerts | Production settings | Background workers, scheduler, API failures, and sync failures are visible. |
| C9-006 | Audit user roles and permissions | Permission report/tests | Minimal roles are enforced and customer data isolation is verified. |
| C9-007 | Triage frontend dependency audit | Dependency update PR/tasks | Known critical/high client vulnerabilities are addressed or documented. |

Production principle:

Do not confuse "works locally" with "ready for a company".

## Phase 10 - Launch Readiness

Objective:

Make the platform usable by Omni directors, staff, and selected customers.

Tasks:

| ID | Task | Output | Acceptance |
| --- | --- | --- | --- |
| C10-001 | Run end-to-end director workflow | QA notes | Director can understand business status and act. |
| C10-002 | Run operations workflow | QA notes | Staff can manage customer, vehicle, tracker, installation, and issue flow. |
| C10-003 | Run customer workflow | QA notes | Customer can log in and inspect their records without confusion. |
| C10-004 | Run invoice/fiscalisation workflow | QA notes | Invoice lifecycle is clear from creation through payment/fiscal status. |
| C10-005 | Run backup restore drill | Restore evidence | Restore procedure is proven. |
| C10-006 | Create launch issue list | Final punch list | Remaining items are prioritized as launch blockers or post-launch tasks. |

Launch principle:

Launch only when the most important real workflows are boringly repeatable.

## Phase 11 - Partner Network Foundation

Objective:

Prepare Omni v4 to support the Omni Certified Partner Network without overbuilding the full regional platform before the Zimbabwe pilot proves the model.

Tasks:

| ID | Task | Output | Acceptance |
| --- | --- | --- | --- |
| C11-001 | Add partner data model | Partner, Partner Level, Partner Territory, Partner Agreement | Omni can distinguish internal users, customers, technicians, certified installers, sales/install partners, Gold Partners, and regional partners. |
| C11-002 | Add partner onboarding workflow | Partner Onboarding Job/checklist | Partner application, KYC, training, test installation, certification, agreement, and activation status are tracked. |
| C11-003 | Link customer onboarding to source partner | `Omni Onboarding Job` + Customer/Lead links | A customer can be attributed to Omni direct sales or a partner without changing customer ownership. |
| C11-004 | Extend installation jobs for partner-submitted work | Installation source, partner, evidence, approval | Partner technicians can submit installation work that Omni approves before activation/billing. |
| C11-005 | Add installation evidence standard | Checklist templates, photo requirements, signoff fields | Wiring/testing/customer handover evidence is captured consistently. |
| C11-006 | Add commission ledger foundation | Partner Commission Rule, Commission Ledger, Partner Payout | Active paid subscriptions can accrue partner commission liabilities even if payouts are initially reviewed manually. |
| C11-007 | Add partner permission boundaries | Roles/API permissions | Partners see only assigned jobs, customers, vehicles, stock, support records, and commission records. |
| C11-008 | Add partner stock and BYOD origin tracking | Tracker/SIM fields and reports | Hardware can be Omni supplied, approved partner supplied, or BYOD while activation remains controlled by Omni. |
| C11-009 | Add partner KPI dashboard | Reports/dashboard | Omni can track active vehicles by partner, net adds, retention, defect rate, tickets per 100 vehicles, churn, and commission liability. |

Partner principle:

Omni owns the customer contract, subscription, data, activation, billing rules, standards, and brand. Partners own local acquisition, installation, first-line support, and relationship assistance within their approved permissions.

Do not build first:

- Full partner marketplace features
- Automatic country expansion logic
- Permanent territory exclusivity
- Broad dealer/provider admin rights for installers
- Complex multi-currency payout automation before the commission model is proven

## Phase 12 - Regional Expansion and Compliance Playbook

Objective:

Turn the partner network into a repeatable regional rollout model once the Zimbabwe pilot and partner economics are validated.

Tasks:

| ID | Task | Output | Acceptance |
| --- | --- | --- | --- |
| C12-001 | Add country launch review checklist | Country Launch Review DocType | Tax, telecom/SIM, data protection, payments, import, licensing, and entity requirements are reviewed before launch. |
| C12-002 | Add territory activation controls | Territory/country status | A country or territory cannot be treated as live until required launch checks are complete or explicitly waived by a director. |
| C12-003 | Add regional partner governance | Regional Partner rules/reports | Regional partner privileges are performance-based and reviewable, not permanent by default. |
| C12-004 | Add cross-border payment controls | Partner payout compliance fields | Commission payouts can record tax documents, withholding notes, payment provider, and reconciliation status. |
| C12-005 | Document repeatable rollout playbook | Operating playbook | A successful market launch can be repeated in another country using the same checklist and standards. |

Regional principle:

Build a network before building branches. Create local entities only when regulation, banking, procurement, staffing, tax, or scale makes them necessary or superior.

## Recommended Execution Order

Start here:

1. Current Workflow Sprint - finish onboarding, enquiry routing, guided installation, customer portal detail/tickets, and role work queues.
2. Phase 5 - Focus Frappe admin experience around those workflows.
3. Phase 6 - Migration rehearsal and cleanup.
4. Phase 7 - Telematics production validation.
5. Phase 8 - ZIMRA readiness.
6. Phase 9 - Production hardening.
7. Phase 10 - Launch readiness.
8. Phase 11 - Partner network foundation.
9. Phase 12 - Regional expansion and compliance playbook.

Already completed or mostly completed:

- Phase 1 - Consolidate project truth.
- Phase 2 - Finalize deployment shape.
- Phase 3 - Build Frappe portal API layer.
- Phase 4 - Wire and polish Svelte customer portal, except dedicated vehicle detail route, responsive QA, and final browser/session validation.

## Immediate Next Actions

These are the first tasks to execute now:

1. Define and implement `Omni Onboarding Job`.
2. Route the public enquiry form into Frappe Lead plus `Omni Onboarding Job`.
3. Add guided `Tracker Installation` transitions, evidence fields, and checklist structure.
4. Add the customer portal vehicle detail route and support ticket detail/history flow.
5. Add role-specific work queues for Directors, Operations Admin, Installation Coordinator, Fleet Manager, and Technician.

Queued immediately after those:

1. Add partner network foundation DocTypes.
2. Link onboarding and installation jobs to partner source where applicable.
3. Add commission ledger foundation.
4. Add partner permission boundaries.
5. Add country launch review checklist.

## Execution Log

### 2026-08-19

Started Phase 1 - Consolidate the Project Truth.

Completed:

- C1-001: Rewrote `README.md` around the active Omni v4 architecture.
- C1-002: Replaced `docs/02_architecture.md` with the current Frappe/ERPNext plus Svelte architecture.
- C1-004: Added `docs/42_omniv4_developer_runbook.md` with local development and verification commands.
- C1-005: Defined active and legacy/reference folders in the README and runbook.

Partially completed:

- C1-003: Legacy v3 areas are labelled in the README and current architecture doc. Remaining work is to add explicit legacy banners to older v3-specific docs if they continue to be used.

Next recommended task:

- C2-001/C2-004: finalize the domain/API/session strategy before expanding the customer portal API.

### 2026-08-19 - Phase 2 Started

Started Phase 2 - Finalize Deployment Shape.

Completed:

- C2-001: Replaced `docs/05_deployment.md` with the Omni v4 domain routing strategy.
- C2-002: Tightened `omni_operations.website_routing` so the public host does not expose `/app`, `/desk`, or Frappe Desk method routes, and the admin host root redirects to the Omni workspace.
- C2-003: Documented preferred and alternate reverse proxy/domain routing shapes.
- C2-004: Added `docs/43_omniv4_portal_api_session_strategy.md` with the portal API/session approach.
- C2-005: Replaced `.env.example` with a v4-focused environment contract and separated legacy v3 values.

Next recommended task:

- C3-001: turn the portal API strategy into the first Frappe API methods and tests.

### 2026-08-19 - Phase 3 Started

Started Phase 3 - Build the Frappe Portal API Layer.

Completed:

- C3-001: Defined the portal API/session contract in `docs/43_omniv4_portal_api_session_strategy.md`.
- C3-002: Implemented `get_current_customer`.
- C3-003: Implemented `get_dashboard_summary`.
- C3-004: Implemented `get_vehicles` and `get_vehicle_detail` with server-side vehicle ownership validation.
- C3-005: Exposed sanitized latest telematics status through portal vehicle responses.
- C3-006: Implemented `get_invoices`.
- C3-007: Implemented `get_documents`.
- C3-008: Implemented `get_support_tickets` and updated support creation to reuse the shared customer scope helper.
- C3-009: Added `run_portal_api_smoke_checks` to verify portal API scoping and endpoint health.

Verified:

- `run_smoke_checks` returned `ok: true`.
- `run_security_smoke_checks` returned `ok: true`.
- `run_portal_api_smoke_checks` returned `ok: true` and confirmed a vehicle from another customer was denied.

Next recommended task:

- C4-001: create a v4 Frappe API client in `client-web` and stop the customer portal depending on old v3 FastAPI route assumptions.

### 2026-08-19 - Phase 4 Started

Started Phase 4 - Wire and Polish the Svelte Customer Portal.

Completed:

- C4-001: Added `client-web/src/lib/api/frappe.ts` and `client-web/src/lib/api/portal.ts` for the v4 Frappe API contract.
- C4-001: Replaced the visible `/login` page's old FastAPI login form with a Frappe sign-in gateway.
- C4-002: Replaced `/portal` with a real customer dashboard shell backed by the v4 portal APIs.
- C4-003: Added a vehicle list view with latest telematics status.
- C4-005: Added invoice list rendering.
- C4-006: Added document list rendering.
- C4-007: Added support ticket list and ticket creation form.
- C4-008: Added loading, signed-out/error, empty, and submission states.

Verified:

- `npm run check` returned 0 errors and 0 warnings.
- `http://localhost:5175/portal` returned HTTP 200 from the running customer portal container.
- `http://localhost:5175/login` returned HTTP 200 from the running customer portal container.

Still open:

- C4-004: add a dedicated vehicle detail route in Svelte.
- C4-009: run a visual/responsive browser pass after the detail route is added.
- Browser-level Frappe session/CORS validation still needs to be tested through the actual routed deployment shape.

### 2026-08-28 - Tracker/SIM Assignment Model

Implemented the future-proof tracker/SIM assignment model discussed during operations workflow design.

Completed:

- Added `Tracker SIM Assignment` as the source of truth for SIM-to-tracker pairing.
- Added `Prepared` status to `Tracker Profile` and `SIM Profile`.
- Supported pre-pairing SIMs to tracker hardware before customer/hub/vehicle onboarding.
- Supported future dual-SIM hardware by allowing separate active tracker slots such as `Primary` and `Secondary`.
- Blocked one SIM from having more than one active assignment.
- Blocked one tracker from having more than one active assignment in the same slot.
- Required customer and vehicle once an assignment reaches `Assigned` or `Installed`.
- Updated `Tracker Installation` so tracker/SIM assignments are created or promoted automatically when an installation is saved.
- Added backfill support so migrated SIM/current-tracker fields become `Tracker SIM Assignment` records.
- Added workspace, permission, access-scope, list-view, runbook, and smoke-check coverage.

Verified:

- `bench --site development.localhost migrate` completed successfully.
- `run_smoke_checks` returned `ok: true`.
- `run_desk_focus_smoke_checks` returned `ok: true`.
- `run_tracker_sim_assignment_smoke_checks` returned `ok: true`.
- Behavioral smoke confirmed:
  - primary prepared SIM assignment is allowed
  - secondary prepared SIM assignment is allowed
  - duplicate active tracker slot is blocked
  - duplicate active SIM assignment is blocked

Current local data:

- `Tracker SIM Assignment`: 10 records
- Assignment states: 6 `Assigned`, 3 `Installed`, 1 `Prepared`

### 2026-08-29 - Partner Expansion Strategy Absorbed

Reviewed `Omni_Regional_Partner_Expansion_Strategy.docx` as source material and folded the useful product implications into this execution plan.

Added:

- Current Workflow Sprint to finish the core operating loop first:
  - `Omni Onboarding Job`
  - public enquiry to Frappe Lead plus Onboarding Job
  - guided installation actions/checklists
  - customer portal vehicle detail and ticket polish
  - role dashboards/work queues
- Partner portal target architecture for `partners.omnilogistics.co.zw`.
- Phase 11 - Partner Network Foundation.
- Phase 12 - Regional Expansion and Compliance Playbook.

Decision:

Do not build the full partner network before the internal Omni operating workflows are reliable. Build partner-ready data structures and attribution once onboarding/installations/customer portal/work queues are complete, then expose a minimal partner portal.

### 2026-08-29 - Omni Onboarding Job Implemented

Started the Current Workflow Sprint and completed W1-001.

Completed:

- Added `Omni Onboarding Job` as the workflow spine for prospect/customer onboarding.
- Added `Omni Onboarding Checklist Item` as a child table for required onboarding tasks.
- Added default checklist tasks for:
  - lead qualification
  - quotation/proposal
  - customer/hub setup
  - vehicle capture
  - installation scheduling
  - portal user provisioning
  - first invoice/billing readiness
- Added readiness flags and automatic progress calculation.
- Added links to ERPNext `Lead`, `Opportunity`, `Quotation`, `Customer`, `Company`, `Sales Invoice`, `User`, plus Omni fleet/install/contract records.
- Added `create_onboarding_job_from_lead` helper for the next public enquiry routing step.
- Added `Onboarding` module registration.
- Added Omni workspace shortcut/card entries for Onboarding Jobs, Leads, Opportunities, Quotations, and Customers.
- Added permission/query hooks so onboarding jobs follow the same customer-scoping model as the rest of Omni operations.
- Added onboarding smoke coverage.

Verified:

- `bench --site development.localhost migrate` completed successfully.
- `run_smoke_checks` returned `ok: true`.
- `run_onboarding_job_smoke_checks` returned `ok: true`.
- `run_desk_focus_smoke_checks` returned `ok: true`.
- `run_portal_api_smoke_checks` returned `ok: true`.
- `run_tracker_sim_assignment_smoke_checks` returned `ok: true`.

Next recommended task:

- W1-002: route the public website enquiry form into ERPNext `Lead` plus `Omni Onboarding Job`.

## Definition of Success

Omni v4 development is considered properly consolidated when:

- A developer can read the README and understand the active architecture in under five minutes.
- Public website, customer portal, and admin app have distinct responsibilities.
- The customer portal is powered by secure Omni/Frappe APIs.
- Frappe Desk is focused around Omni operations rather than generic ERP clutter.
- v3 code is clearly marked as legacy/reference.
- Production deployment, migration, telematics, fiscalisation, permissions, and backups all have testable acceptance criteria.
