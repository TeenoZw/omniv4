# 38 - Omni v4 Production Readiness

## Purpose

This checklist tracks the remaining work needed before Omni v4 can move from local ERPNext evaluation into a production-ready business platform.

## Priority Order

1. Finish real telematics provider validation.
2. Complete live ZIMRA onboarding and fiscalisation certification.
3. Rehearse the final v3 migration from a fresh export.
4. Harden production deployment, backups, monitoring, and access control.

## Telematics

Current status:

- Universal telematics account/link/log model exists.
- Wialon-compatible adapter has been added as the first real provider implementation.
- Desk actions exist for account connection checks and unit syncs.
- Unit sync can update latest coordinates/speed when the linked unit is sync-enabled.
- Provider accounts support system-wide, regional admin, and customer hub scopes so a parent Wialon token can sync many customer vehicles without duplicating credentials.

Still required:

- Add the chosen real Wialon or other provider admin credentials to a correctly scoped `Telematics Provider Account`.
- Run `Check Connection` against the live provider.
- Import or create real `Telematics Unit Link` records.
- Match external unit ids to Omni vehicles and verify each linked vehicle has the correct Omni customer.
- Run live `Sync Units`.
- Confirm latest position data appears in Desk and customer portal for authorized customers only.
- Decide the production sync schedule and rate limits.

Acceptance:

- At least one real provider account is active.
- At least one real vehicle receives latest position data.
- Failed provider calls produce useful `Telematics Sync Log` entries.
- Switching to a second provider only requires a new adapter, not fleet model changes.

## ZIMRA Fiscalisation

Current status:

- Fiscalisation DocTypes and planned flow are captured in the project plan.
- The official ZIMRA Fiscal Device Gateway API v7.2 has been reviewed.
- Omni fiscalisation DocTypes now include FDMS-specific fields for device model headers, certificates, device serial/config, fiscal day status, receipt global numbers, operation IDs, QR data, and signatures.
- The detailed execution plan is captured in `docs/39_zimra_fdms_api_execution_plan.md`.
- ZIMRA live submission remains blocked until onboarding details, credentials, certificates, and environment access are available.

Still required:

- Confirm the official ZIMRA fiscalisation path for the company.
- Register the company/device/software and confirm the device model name/version registered with ZIMRA.
- Obtain test or production device ID and activation key.
- Generate CSR/private key material and complete `registerDevice`.
- Store the FDMS-issued device certificate and certificate expiry.
- Implement the live `ZimraFDMSProvider` adapter with mutual TLS.
- Implement `verifyTaxpayerInformation`, `registerDevice`, `getServerCertificate`, `getConfig`, `getStatus`, `openDay`, `submitReceipt`, and `closeDay`.
- Validate invoice submission, receipt numbers, QR/signature payloads, credit notes, retry handling, and offline recovery.
- Keep accounting documents usable even when fiscalisation is pending or failed, with clear status labels.

Acceptance:

- A submitted ERPNext Sales Invoice can be fiscalised through the official ZIMRA path.
- Fiscalisation status, request id, response id, QR/signature, and errors are stored against the invoice/fiscal document.
- Failed submissions are retryable and auditable.

## v3 Migration

Current status:

- Supabase export files were staged and imported into the local evaluation bench.
- Core customers, vehicles, drivers, trackers, SIMs, installations, provider units, documents, and contracts have been mapped into Omni structures.

Still required:

- Take a fresh full export from the v3 Supabase database.
- Re-run import into a clean site.
- Compare source row counts with migrated Omni row counts.
- Check duplicate handling, required fields, missing references, and inactive records.
- Freeze final migration mappings before production cutover.

Acceptance:

- A clean migration run produces repeatable results.
- No critical source tables are unaccounted for.
- Customer portal records match the expected customer scope.
- Migration logs make skipped/failed rows obvious.

## Deployment Hardening

Target domains:

- Public landing website: `www.omnilogistics.co.zw`
- Customer portal: a separately deployable customer-facing app presented as an extension of the public website, for example `www.omnilogistics.co.zw/portal` or a portal-specific host.
- Internal admin app: Frappe/ERPNext on `admin.omnilogistics.co.zw`

Still required:

- Choose production hosting target.
- Pin supported MariaDB, Redis, Python, Node, Frappe, and ERPNext versions.
- Configure HTTPS, domain, email, file storage, backups, and restore drills.
- Configure host-based routing so the admin Desk is only presented on `admin.omnilogistics.co.zw`.
- Deploy the public website independently from Frappe.
- Deploy the customer portal independently from Frappe, backed by a narrow Frappe API adapter.
- Add redirects so `/app` and other admin routes do not become the public website's first impression.
- Disable development credentials and sample/test users.
- Enforce role-based access for directors, operations users, technicians, and customer portal users.
- Set up background workers, scheduler, logs, alerts, and error monitoring.
- Define backup retention and disaster recovery procedure.

Acceptance:

- Production can be rebuilt from source plus documented secrets.
- Backups are automated and a restore has been tested.
- Scheduler and background workers are healthy.
- No sample data or shared test passwords remain.

## UI Readiness

Public/customer-facing structure:

- `www.omnilogistics.co.zw` should be the public Omni Logistics website.
- The customer portal should feel like part of that public website, not like ERPNext Desk, and should be separately deployable from the admin app.
- `admin.omnilogistics.co.zw` should remain the internal/admin application for directors and staff.

Still required:

- Polish Desk workspaces for the minimum roles:
  - Directors / Omni Operations Admin
  - Fleet Manager
  - Installation Coordinator
  - Technician
  - Customer Portal User
- Keep the first navigation simple:
  - Operations
  - Sales
  - Purchasing
  - Inventory
  - Finance
  - People
  - Administration
- Keep customer portal focused on the jobs customers actually check:
  - vehicles
  - tracker status
  - maintenance
  - documents
  - contracts
  - invoices
  - support
- Avoid exposing ERPNext complexity until a user needs it.

Acceptance:

- A director can understand company status from the dashboard.
- Operations users can move from customer to vehicle to tracker/installation without hunting.
- Customers only see their own records.
- Mobile portal views remain readable and uncluttered.
