# 47 - Omni v4 Launch Acceptance Report

Last verified: 2026-10-19

This report records the production evidence for the first six launch-readiness workstreams. It complements the product plan and replaces older Render-specific deployment assumptions with the active Contabo VPS architecture.

## 1. Customer Portal Acceptance

Status: **Passed**

- Verified production login, legal acceptance, customer-scoped dashboard, vehicle detail, support ticket creation, ticket history, page refresh, session persistence, visible sign out, and signed-out redirect.
- Verified that portal APIs deny access to another customer's vehicles and tickets.
- Verified the production launch suite passes all portal isolation checks.
- Removed the temporary browser-test user, legal acceptance, contact link, and support ticket after acceptance.

## 2. Commercial Workflow Acceptance

Status: **Passed**

- Executed the production chain: Quotation -> Sales Order -> Sales Invoice -> Payment Entry.
- Verified an USD 80 invoice using the current commercial rates: USD 70 4G tracker, USD 10 monthly service, and zero-priced SIM/installation lines.
- Verified the payment reduced outstanding value to zero.
- Verified invoice PDF generation and outgoing email configuration.
- Verified smoke-test commercial records are removed after the run.
- Stock items now resolve a valid company warehouse before Sales Order creation.

## 3. Installation Workflow Acceptance

Status: **Implemented; final human walkthrough pending**

- Completion is only allowed from `In Progress` for an existing installation.
- Completion requires technician, scheduled date, completed date, location, work performed, customer sign-off, and either an installation photo or completion attachment.
- The Complete action is only shown while the installation is in progress.
- Focused automated tests cover missing evidence and successful photo evidence.
- Production test execution remains disabled by design. Do not enable the Frappe test runner on the live site; perform the final technician walkthrough with a real installation record.

## 4. Wialon Production Validation

Status: **Blocked by provider credentials**

- The production scheduler and two workers are online.
- Existing ownership reconciliation is intact: activated provider accounts and 14 linked vehicles have no reported ownership conflicts.
- Live hierarchy/unit synchronization currently returns Wialon API error 8 during token login.
- Replace or renew the token on `Omnitrack Master`, run Check Connection, then run Discover Hierarchy and Sync Units.
- Acceptance requires one newly discovered account/unit, confirmed customer ownership, current telemetry, a successful sync log, and a deliberate failed-call log.

## 5. v3 Migration Rehearsal

Status: **Current export validated; final cutover export pending**

- Re-ran transformation and validation from the staged 2026-08-17 Supabase export.
- Validated output: 6 customers, 6 profiles, 26 trackers, 10 SIMs, 11 vehicles, 12 installations, 2 enquiries, and 5 subscriptions.
- The current staged export is missing `vehicles_rows.csv`, `device_pairings_rows.csv`, and `technician_jobs_rows.csv`; mapped output was reconstructed from the available assignment data.
- Final acceptance requires a fresh full Supabase export, import into a clean production-candidate site, source/destination reconciliation, ownership sampling, inactive-record checks, and a second repeatable run.

## 6. Infrastructure Hardening

Status: **Core controls passed; external destinations pending**

- Contabo production services are running behind Cloudflare on the public, portal, and admin hosts.
- Frappe scheduler is enabled and two workers are online.
- Daily encrypted backup and five-minute health timers are enabled and active.
- A real isolated restore drill passed and restored 801 DocTypes.
- Only `Administrator` currently has the `System Manager` role.
- Deployed versions are pinned at Frappe 15.118.0, ERPNext 15.119.2, MariaDB 10.11.19, and Redis 7.2.16.
- SMTP is configured through the default outgoing Email Account.
- Remaining hardening: configure `BACKUP_REMOTE` for off-server encrypted copies, configure `HEALTHCHECK_WEBHOOK_URL` for external alerts, and choose an error-monitoring destination.

## Launch Decision

The portal and core commercial workflow are production-functional. Do not call the complete launch finished until these external dependencies are closed:

1. Renew the Wialon production token and pass live discovery/sync acceptance.
2. Provide a fresh complete Supabase export and pass the clean-site migration rehearsal.
3. Configure off-server backup replication and external health/error alerts.
4. Complete one real technician installation from scheduling through signed completion.

