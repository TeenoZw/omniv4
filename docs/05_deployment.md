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

## Current Cloudflare Setup

Created on 2026-09-02:

- Public Cloudflare Pages project: `omniv4-web`
  - Source repo: `TeenoZw/omniv4`
  - Source branch: `main`
  - Build root: `client-web`
  - Build command: `npm run build`
  - Build output: `.svelte-kit/cloudflare`
  - Pages URL: `https://omniv4-web.pages.dev`
  - Preview custom domain: `https://v4.omnilogistics.co.zw`
- Customer portal Cloudflare Pages project: `omniv4-portal`
  - Source repo: `TeenoZw/omniv4`
  - Source branch: `main`
  - Build root: `client-web`
  - Build command: `npm run build`
  - Build output: `.svelte-kit/cloudflare`
  - Pages URL: `https://omniv4-portal.pages.dev`
  - Preview custom domain: `https://portal-v4.omnilogistics.co.zw`

Current cutover notes:

- `www.omnilogistics.co.zw` still points to the old `omniv3.pages.dev` Pages project until final cutover.
- `admin.omnilogistics.co.zw` still points to the old `admin-web-erz.pages.dev` Pages project until the Frappe admin cutover is ready.
- `api.omnilogistics.co.zw` still points to the old Render API until the Frappe API is live.
- Render staging will use `admin-v4.omnilogistics.co.zw` for Frappe/ERPNext validation before production cutover.
- Do not move `www`, `admin`, or `api` until the Render staging site, Frappe backups, and customer portal API checks are complete.
- `portal-v4.omnilogistics.co.zw` is a safe preview hostname. The production portal hostname or `/portal` path should be assigned only after the Frappe API is live.
- The v4 Cloudflare Pages preview projects currently point API/admin links at `https://admin-v4.omnilogistics.co.zw`; this hostname will become active after Render staging is created and DNS is added.

## Render Staging Decision

The current infrastructure decision is:

- Cloudflare Pages hosts the public v4 preview and customer portal preview.
- Render is used as a staging home for the Frappe/ERPNext admin app.
- Render staging is not treated as final production until the full Frappe stack proves reliable with backups, workers, scheduler, MariaDB persistence, and real portal API traffic.

Recommended staging hostname:

```text
admin-v4.omnilogistics.co.zw -> Render Frappe/ERPNext staging service
```

Expected Render services:

1. Frappe web service running the admin app.
2. Frappe worker service for queues.
3. Frappe scheduler service.
4. MariaDB service with persistent disk.
5. Redis service.
6. Persistent storage for Frappe public/private files, or an external object storage decision before production.

Render staging acceptance:

- `admin-v4.omnilogistics.co.zw` loads Frappe Desk over HTTPS.
- `omni_operations` is installed and migrated.
- Scheduler and workers are running.
- MariaDB data persists across service restarts.
- A database backup and restore rehearsal is completed.
- Customer portal API smoke checks pass against the Render-hosted Frappe API.
- No v3 live DNS records are changed until these checks pass.

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
