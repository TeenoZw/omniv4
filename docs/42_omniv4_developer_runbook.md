# 42 - Omni v4 Developer Runbook

## Purpose

This runbook captures the day-to-day commands for developing and checking Omni v4 locally.

## Project Surfaces

| Surface | Path | Local URL |
| --- | --- | --- |
| Public website | `client-web` | `http://localhost:5174` |
| Customer portal | `client-web` | `http://localhost:5175/portal` |
| Frappe admin | `erpnext-eval/frappe_docker/development/frappe-bench` | `http://development.localhost:8000/app/omni-operations` |

## Start Public Website and Customer Portal

From the repo root:

```bash
docker compose -f docker-compose.omniv4-surfaces.yml up --build
```

Default ports:

- public website: `5174`
- customer portal: `5175`

Override ports if needed:

```bash
OMNI_PUBLIC_PORT=5184 OMNI_PORTAL_PORT=5185 docker compose -f docker-compose.omniv4-surfaces.yml up --build
```

Check container status:

```bash
docker compose -f docker-compose.omniv4-surfaces.yml ps
```

Stop the surfaces:

```bash
docker compose -f docker-compose.omniv4-surfaces.yml down
```

## Run Svelte Checks

```bash
cd client-web
npm run check
```

Optional checks:

```bash
cd client-web
npm run lint
npm run test
```

## Start or Inspect Frappe Docker Evaluation Stack

From the Frappe Docker folder:

```bash
cd erpnext-eval/frappe_docker
docker compose -f devcontainer-example/docker-compose.yml -p omni-erpnext-eval ps
```

If the stack is stopped:

```bash
cd erpnext-eval/frappe_docker
docker compose -f devcontainer-example/docker-compose.yml -p omni-erpnext-eval up -d
```

Open a shell in the Frappe container:

```bash
cd erpnext-eval/frappe_docker
docker compose -f devcontainer-example/docker-compose.yml -p omni-erpnext-eval exec frappe bash
```

Run bench commands inside the container:

```bash
cd /workspace/development/frappe-bench
bench --site development.localhost list-apps
```

## Start Frappe Bench

Inside the Frappe container:

```bash
cd /workspace/development/frappe-bench
bench start
```

Expected local admin URL:

```text
http://development.localhost:8000/app/omni-operations
```

## Frappe Smoke Checks

From the host:

```bash
cd erpnext-eval/frappe_docker
docker compose -f devcontainer-example/docker-compose.yml -p omni-erpnext-eval exec -T frappe bash -lc 'cd /workspace/development/frappe-bench && bench --site development.localhost execute omni_operations.omni_setup.smoke.run_smoke_checks'
```

Desk-focused smoke checks:

```bash
cd erpnext-eval/frappe_docker
docker compose -f devcontainer-example/docker-compose.yml -p omni-erpnext-eval exec -T frappe bash -lc 'cd /workspace/development/frappe-bench && bench --site development.localhost execute omni_operations.omni_setup.smoke.run_desk_focus_smoke_checks'
```

Customer portal API smoke checks:

```bash
cd erpnext-eval/frappe_docker
docker compose -f devcontainer-example/docker-compose.yml -p omni-erpnext-eval exec -T frappe bash -lc 'cd /workspace/development/frappe-bench && bench --site development.localhost execute omni_operations.omni_setup.smoke.run_portal_api_smoke_checks'
```

Tracker/SIM assignment smoke checks:

```bash
cd erpnext-eval/frappe_docker
docker compose -f devcontainer-example/docker-compose.yml -p omni-erpnext-eval exec -T frappe bash -lc 'cd /workspace/development/frappe-bench && bench --site development.localhost execute omni_operations.omni_setup.smoke.run_tracker_sim_assignment_smoke_checks'
```

Telematics scheduler checks:

```bash
cd erpnext-eval/frappe_docker
docker compose -f devcontainer-example/docker-compose.yml -p omni-erpnext-eval exec -T frappe bash -lc 'cd /workspace/development/frappe-bench && bench --site development.localhost scheduler status && bench --site development.localhost doctor'
```

Run the automatic Wialon/unit sync task manually:

```bash
cd erpnext-eval/frappe_docker
docker compose -f devcontainer-example/docker-compose.yml -p omni-erpnext-eval exec -T frappe bash -lc 'cd /workspace/development/frappe-bench && bench --site development.localhost execute omni_operations.telematics.scheduled.sync_enabled_provider_accounts'
```
```

The scheduled task runs hourly when the Frappe scheduler is enabled and workers are online. It syncs only active `Telematics Provider Account` records where `Sync Enabled` is checked.

## Migration Tooling

Validate migration templates:

```bash
python3 scripts/validate_migration_templates.py
```

Transform staged v3 exports:

```bash
python3 scripts/transform_v3_exports.py
```

Generate telematics unit export helper output:

```bash
python3 scripts/generate_telematics_unit_export.py
```

Migration working output currently lives under:

```text
migration_working
```

## Current Architecture Rule

Do v4 product work in:

- `client-web`
- `erpnext-eval/frappe_docker/development/frappe-bench/apps/omni_operations`
- `docs`
- `scripts`

Treat these as legacy/reference unless explicitly revived:

- `backend`
- `admin-web`

## Common Verification Checklist

Before saying a change is ready:

1. Run the relevant Frappe smoke check if the change touches `omni_operations`.
2. Run `npm run check` if the change touches `client-web`.
3. Confirm the public site still opens at `http://localhost:5174`.
4. Confirm the portal still opens at `http://localhost:5175/portal`.
5. Confirm admin still routes to `http://development.localhost:8000/app/omni-operations` when the bench is running.
6. For Wialon/telematics changes, confirm scheduler status and inspect the latest `Telematics Sync Log`.
7. Update the relevant docs if behavior, commands, domains, or ownership changed.
