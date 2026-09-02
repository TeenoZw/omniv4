# 45 - Render Staging Runbook

## Purpose

This runbook defines how Omni v4 should use Render for staging while Cloudflare continues to host the public and portal previews.

Render staging exists to prove the Frappe/ERPNext admin app before moving the real `admin.omnilogistics.co.zw` DNS record away from the old deployment.

## Target Shape

```text
Cloudflare Pages
├── v4.omnilogistics.co.zw
│   └── omniv4-web
└── portal-v4.omnilogistics.co.zw
    └── omniv4-portal

Cloudflare DNS
└── admin-v4.omnilogistics.co.zw
    └── Render Frappe/ERPNext staging stack
```

## Render Services

Create the Render staging stack as separate services, not as one all-in-one process.

| Service | Render type | Purpose |
| --- | --- | --- |
| `omniv4-frappe-web` | Web Service | Frappe HTTP app for Desk and API. |
| `omniv4-frappe-worker` | Background Worker | Long-running Frappe queue workers. |
| `omniv4-frappe-scheduler` | Background Worker or Cron-backed worker | Frappe scheduled tasks. |
| `omniv4-mariadb` | Private Service with persistent disk | Frappe/ERPNext database. |
| `omniv4-redis-cache` | Redis / Key Value | Cache and realtime support. |
| `omniv4-redis-queue` | Redis / Key Value | Queue backend. |

## Minimum Staging Requirements

- Use paid Render services for anything that must stay awake.
- MariaDB must have a persistent disk.
- Frappe private/public files must have persistent storage before real customer documents are uploaded.
- Do not store production secrets in GitHub.
- Do not use the old FastAPI `backend` as the v4 API. Customer portal API calls should go to Frappe methods.

## Environment Values

Use Render environment variables or secret files for:

```text
FRAPPE_SITE_NAME=admin-v4.omnilogistics.co.zw
ERPNEXT_VERSION=version-15
FRAPPE_VERSION=version-15
MYSQL_ROOT_PASSWORD=<secret>
MYSQL_PASSWORD=<secret>
ADMIN_PASSWORD=<secret>
REDIS_CACHE_URL=<render-private-url>
REDIS_QUEUE_URL=<render-private-url>
SOCKETIO_PORT=9000
```

Provider credentials must be entered only after staging is secured:

```text
TELEMATICS_PROVIDER_TOKEN=<secret>
ZIMRA credentials/certificates=<secret>
SMTP credentials=<secret>
```

## Cloudflare DNS After Render Is Ready

When Render gives the staging hostname, create:

```text
admin-v4.omnilogistics.co.zw CNAME <render-hostname>
```

Keep the record proxied through Cloudflare if the Render service works cleanly behind the proxy. If websockets or large uploads misbehave, test DNS-only mode before changing app code.

Do not change:

```text
www.omnilogistics.co.zw
admin.omnilogistics.co.zw
api.omnilogistics.co.zw
```

until staging acceptance passes.

## Deployment Steps

1. Create the Render services.
2. Build or select a Frappe/ERPNext Docker image that includes `omni_operations`.
3. Create the Frappe site `admin-v4.omnilogistics.co.zw`.
4. Install ERPNext and `omni_operations`.
5. Run migrations.
6. Configure Omni setup fixtures, roles, workspaces, warehouses, and defaults.
7. Confirm Frappe Desk loads on the Render service URL.
8. Point `admin-v4.omnilogistics.co.zw` to Render through Cloudflare.
9. Update Cloudflare Pages v4 preview environment variables to use:

```text
VITE_API_URL=https://admin-v4.omnilogistics.co.zw/api/method
VITE_ADMIN_URL=https://admin-v4.omnilogistics.co.zw
```

10. Run smoke checks.

## Smoke Checks

Inside the Frappe environment:

```bash
bench --site admin-v4.omnilogistics.co.zw execute omni_operations.omni_setup.smoke.run_smoke_checks
bench --site admin-v4.omnilogistics.co.zw execute omni_operations.omni_setup.smoke.run_desk_focus_smoke_checks
bench --site admin-v4.omnilogistics.co.zw execute omni_operations.omni_setup.smoke.run_onboarding_job_smoke_checks
bench --site admin-v4.omnilogistics.co.zw execute omni_operations.omni_setup.smoke.run_tracker_sim_assignment_smoke_checks
bench --site admin-v4.omnilogistics.co.zw execute omni_operations.omni_setup.smoke.run_portal_api_smoke_checks
```

## Staging Acceptance

Staging is acceptable only when:

- Frappe Desk loads at `admin-v4.omnilogistics.co.zw`.
- The Omni Operations workspace is visible and focused.
- Customer/hub onboarding works from prerequisites through portal user provisioning.
- Tracker/SIM assignment supports prepared, reserved, assigned, installed, and dual-SIM paths.
- The portal can call the Frappe API without CORS/session failures.
- Customers only see their own records.
- Scheduler and workers are healthy.
- MariaDB data survives restarts.
- Backup and restore has been rehearsed once.

## Production Cutover

Only after staging acceptance:

1. Export fresh v3 Supabase data.
2. Run a clean migration into staging or a fresh production Frappe site.
3. Verify row counts, customer scope, invoices, vehicles, trackers, SIMs, and portal access.
4. Move `www.omnilogistics.co.zw` to `omniv4-web`.
5. Move the chosen portal hostname/path to `omniv4-portal`.
6. Move `admin.omnilogistics.co.zw` to the Frappe admin service.
7. Retire or freeze the old v3 services after a rollback window.
