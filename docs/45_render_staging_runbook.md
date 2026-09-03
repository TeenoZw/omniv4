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

Use a compact all-in-one Frappe staging service first. This is intentional for Render because Frappe web, workers, scheduler, generated assets, and private/public files all need a shared `sites` path. Render disks are attached to one service at a time, so splitting Frappe into several services before external file storage is chosen would make the staging setup fragile.

| Service | Render type | Purpose |
| --- | --- | --- |
| `omniv4-frappe-staging` | Web Service | Frappe Desk/API plus staging workers and scheduler in one container. |
| `omniv4-mariadb` | Private Service with persistent disk | Frappe/ERPNext database. |
| `omniv4-redis` | Redis / Key Value | Cache, queue, and realtime support for staging. |

The Blueprint template lives at:

```text
deploy/render/render.yaml
```

The Frappe image and startup entrypoint live at:

```text
deploy/render/frappe.Dockerfile
deploy/render/start-frappe-staging.sh
```

## Minimum Staging Requirements

- A Render Hobby workspace is acceptable for staging, but the services still need billing/payment information enabled because Frappe requires paid resources for persistent disks.
- Use paid Render services for anything that must stay awake.
- Do not use free Render services for Frappe staging; free services cannot attach the persistent disks needed for Frappe `sites` files and MariaDB data.
- MariaDB must have a persistent disk.
- Frappe private/public files must have persistent storage before real customer documents are uploaded.
- Treat the all-in-one Frappe process as staging only. Before production, either move to a VPS/container host that supports shared volumes between services or move Frappe file storage to object storage and split web, workers, scheduler, and websocket cleanly.
- Do not store production secrets in GitHub.
- Do not use the old FastAPI `backend` as the v4 API. Customer portal API calls should go to Frappe methods.

## Environment Values

Use Render environment variables or secret files for:

```text
FRAPPE_SITE_NAME=admin-v4.omnilogistics.co.zw
PORT=8000
MYSQL_ROOT_PASSWORD=<secret>
ADMIN_PASSWORD=<secret>
DB_HOST=<render-private-mariadb-host>
DB_PORT=3306
REDIS_CACHE=<render-redis-connection-string>
REDIS_QUEUE=<render-redis-connection-string>
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

1. Confirm the Render API token works:

```bash
scripts/render_check_token.sh /absolute/path/to/render-token-file
```

2. Create the Render Blueprint from `deploy/render/render.yaml`.
3. Enter the required secret values in Render:

```text
MYSQL_ROOT_PASSWORD
MARIADB_ROOT_PASSWORD
ADMIN_PASSWORD
TELEMATICS_PROVIDER_TOKEN
```

4. Deploy `omniv4-frappe-staging`.
5. Confirm the startup script creates the site `admin-v4.omnilogistics.co.zw`, installs ERPNext, installs `omni_operations`, and runs migrations.
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
