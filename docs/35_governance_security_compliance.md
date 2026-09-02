# 35 - Governance, Security, and Compliance

## Purpose

This document records the first governance decisions for Omni v4 while it is being built as a Frappe app on ERPNext.

## GPL / Commercial Packaging

ERPNext is licensed under GPLv3. Omni v4 is currently being built as a separate Frappe app installed alongside ERPNext.

Working decision:

- Use ERPNext as an upstream open-source platform.
- Keep Omni-specific business logic inside `omni_operations`.
- Do not copy ERPNext source into another non-Frappe application.
- Do not remove ERPNext copyright, license, or attribution notices.
- Before commercial distribution, get legal review on GPLv3 obligations.
- For hosted/SaaS use, keep a clear internal record of ERPNext modifications and Omni app changes.

Practical implication:

- Internal use and hosted evaluation are acceptable for now.
- Distribution of a combined product or modified ERPNext build needs legal review before launch.

## Role Permission Direction

Minimal launch roles:

- `Omni Operations Admin`
- `Fleet Manager`
- `Installation Coordinator`
- `Technician`
- `Customer Portal User`
- `System Manager`

Permission intent:

| Role | Intent |
| --- | --- |
| System Manager | Full system administration and emergency repair. |
| Omni Operations Admin | Full Omni operations control without needing full Frappe system ownership. |
| Fleet Manager | Manage vehicles, drivers, assignments, telematics links, maintenance, and customer fleet health. |
| Installation Coordinator | Schedule and update installations, assignments, tracker/SIM records, and maintenance coordination. |
| Technician | Read assigned operational records and update installation/maintenance work performed. |
| Customer Portal User | Portal-only access to their own customer fleet, invoices, payments, tickets, and tracking handoff. |

Implementation rule:

- Desk users should get only the DocTypes needed for their workflows.
- Customer portal users should not have Desk access.
- Provider credentials, fiscal credentials, and system settings should be limited to `System Manager` and `Omni Operations Admin`.
- As soon as real customer data is loaded, customer-facing queries must filter by the logged-in user's linked customer.

## Audit Strategy

Use Frappe's native audit primitives first:

- `track_changes` on Omni operational DocTypes.
- Frappe Version records for field-level changes.
- DocType timeline and comments for user-visible operational history.
- Submitted ERPNext documents for accounting and stock immutability.
- Dedicated sync log DocTypes for integrations.

Current Omni audit DocTypes:

- `Telematics Sync Log`

Planned audit DocTypes:

- `Fiscal Sync Log`
- Optional `Omni Activity Log` only if native Frappe Version records are not enough.

Audit rules:

- Never store raw API secrets in logs.
- Store request/response summaries, status, timestamps, record counts, and error messages.
- For external integrations, keep provider-specific payloads short and redacted unless they are required for certification.
- Submitted financial and stock records should be corrected with reversal/credit workflows, not edited silently.

## Compliance Record Mapping

Existing Omni v3 compliance concepts should map into v4 as follows:

| v3 Area | v4 Direction |
| --- | --- |
| Vehicle licences | Omni custom vehicle compliance fields or future `Vehicle Compliance Document`. |
| Insurance | Document attachment linked to Fleet Vehicle and Customer Fleet Profile. |
| Vehicle registration | Fleet Vehicle fields plus document attachment. |
| Tax certificates | Document attachment linked to Company or Customer. |
| Fiscalisation | Track J fiscalisation DocTypes and ERPNext Sales Invoice links. |
| Integration logs | Provider-specific sync log DocTypes. |
| Admin activity logs | Frappe Version and Activity Log first; custom log only if needed. |

## Immediate Security Gaps

- Portal customer filtering is only a first-pass fallback and must be hardened before production.
- Fiscalisation credentials are planned but not implemented.
- Telematics credentials currently use Frappe password fields but need production review.
- Role permissions are broad during evaluation and should be tightened before real customer onboarding.
