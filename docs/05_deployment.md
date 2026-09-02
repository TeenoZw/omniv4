# 05 - Omni v4 Deployment and Operations

## Purpose

This guide describes the intended Omni v4 deployment shape.

The old v3 deployment model used a FastAPI backend, a custom admin web app, and a customer web app. Omni v4 now targets Frappe/ERPNext for the admin/business engine and Svelte for the public/customer-facing surfaces.

## Production Surfaces

| Surface | Domain | Runtime | Responsibility |
| --- | --- | --- | --- |
| Public website | `www.omnilogistics.co.zw` | Svelte `client-web` | Brand, services, lead capture, portal entry. |
| Customer portal | `www.omnilogistics.co.zw/portal` preferred, or `portal.omnilogistics.co.zw` | Svelte `client-web` | Customer dashboard, vehicles, trackers, invoices, documents, support. |
| Admin app | `admin.omnilogistics.co.zw` | Frappe/ERPNext + `omni_operations` | Directors, staff, ERP, fleet, telematics, maintenance, fiscalisation, reports. |
| Omni API | Frappe API path, usually on the admin/API host | Frappe methods | Narrow customer portal and integration APIs. |

## Recommended Routing

Preferred:

```text
www.omnilogistics.co.zw           -> Svelte public site
www.omnilogistics.co.zw/portal    -> Svelte customer portal
admin.omnilogistics.co.zw         -> Frappe/ERPNext Desk
admin.omnilogistics.co.zw/api     -> Frappe API
```

Acceptable alternative:

```text
www.omnilogistics.co.zw           -> Svelte public site
portal.omnilogistics.co.zw        -> Svelte customer portal
admin.omnilogistics.co.zw         -> Frappe/ERPNext Desk and API
```

Decision:

- Prefer `www.omnilogistics.co.zw/portal` for customers because the portal should feel like an extension of the public website.
- Keep `admin.omnilogistics.co.zw` reserved for directors and staff.

## Local Development

Start the Svelte public and portal surfaces:

```bash
docker compose -f docker-compose.omniv4-surfaces.yml up --build
```

Default local URLs:

```text
http://localhost:5174
http://localhost:5175/portal
```

The local Frappe bench is documented in:

```text
erpnext-eval/README.md
docs/42_omniv4_developer_runbook.md
```

## API and Session Strategy

The customer portal should use narrow Frappe/Omni APIs. It should not call broad ERPNext Desk routes.

Recommended API base:

```text
https://admin.omnilogistics.co.zw/api/method
```

Local API base:

```text
http://development.localhost:8000/api/method
```

Session options:

1. Same-site proxy path:
   - Public and portal are served from `www.omnilogistics.co.zw`.
   - API requests are proxied from `/api/*` to Frappe.
   - This gives the cleanest browser behavior for cookies and CORS.

2. Cross-subdomain API:
   - Portal runs on `www` or `portal`.
   - API runs on `admin`.
   - Requires explicit CORS, cookie, CSRF, and credential handling.

Recommended path:

- Use a same-site proxy for portal API calls where possible.
- Keep Frappe admin on `admin.omnilogistics.co.zw`.
- Do not expose customer workflows through Desk routes.

## Environment Variables

Shared public/customer app:

```bash
VITE_OMNI_SURFACE=public
VITE_API_URL=https://admin.omnilogistics.co.zw/api/method
VITE_PUBLIC_SITE_URL=https://www.omnilogistics.co.zw
VITE_PORTAL_URL=https://www.omnilogistics.co.zw/portal
VITE_ADMIN_URL=https://admin.omnilogistics.co.zw
```

Local Svelte surfaces:

```bash
OMNI_PUBLIC_PORT=5174
OMNI_PORTAL_PORT=5175
OMNI_PUBLIC_API_URL=http://development.localhost:8000/api/method
OMNI_PORTAL_API_URL=http://development.localhost:8000/api/method
```

Frappe secrets and provider credentials should be stored in Frappe site configuration, environment secrets, or the chosen production secret store.

Do not commit:

- Wialon or telematics tokens
- ZIMRA credentials
- certificates or private keys
- production database passwords
- administrator passwords

## Frappe Production Requirements

Before production:

1. Pin supported Frappe and ERPNext versions.
2. Pin MariaDB, Redis, Python, and Node versions.
3. Configure HTTPS.
4. Configure email.
5. Configure background workers and scheduler.
6. Configure backups and restore drills.
7. Configure file storage.
8. Configure logs, monitoring, and alerts.
9. Disable sample/test users.
10. Verify role-based access and customer portal scoping.

## Backup and Restore

Production must have:

- automated database backups
- automated private/public file backups
- backup retention policy
- documented restore command
- at least one tested restore before launch

No production launch should happen until restore has been tested.

## Security Minimums

1. Admin app is only presented on `admin.omnilogistics.co.zw`.
2. Portal APIs enforce customer scoping server-side.
3. CORS is restricted to known domains.
4. Telematics and fiscalisation secrets are never committed.
5. Customer portal users cannot access Desk unless explicitly permitted.
6. Test users and demo records are removed before launch.
7. Frontend dependency vulnerabilities are triaged before production.

## Current Local Status

Current local development uses:

- Frappe/ERPNext version 15 evaluation bench.
- `omni_operations` custom app.
- Svelte public and customer portal surfaces from `client-web`.

Current production blockers are tracked in:

```text
docs/38_omniv4_production_readiness.md
docs/40_omniv4_consolidation_execution_plan.md
```

