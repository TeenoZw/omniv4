# 47 - Omni v4 Launch Acceptance Report

Last verified: 2026-11-11

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

Status: **Passed**

- The renewed `Omnitrack Master` token connects successfully through `https://hst-api.wialon.eu`.
- Production validation workflow run `42981769390`, attempt 2, passed connection, hierarchy discovery, unit synchronization, activated-account reconciliation, scheduler, and worker checks.
- Discovery processed 12 accounts, 13 users, and 15 units with no new records required: all current provider records were already known. Fourteen units were updated and one configured test unit was ignored.
- All 14 linked production units report successful synchronization and customer ownership. A live sample confirmed `Toyota Probo` is linked to `Nenzou Hub` and vehicle `AHO8444`, with position data and a current successful sync timestamp.
- Successful connection and discovery evidence is stored in sync logs `TSL-2026-4140` through `TSL-2026-4143`. The earlier rejected-token log `TSL-2026-4138` proves failed-call logging without altering customer or vehicle mappings.
- The scheduler is enabled and two workers are online.
- `.github/workflows/validate-wialon-production.yml` provides a repeatable, token-safe production acceptance check.

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

1. Provide a fresh complete Supabase export and pass the clean-site migration rehearsal.
2. Configure off-server backup replication and external health/error alerts.
3. Complete one real technician installation from scheduling through signed completion.

