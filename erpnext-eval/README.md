# ERPNext Evaluation Lane

This folder tracks the disposable ERPNext/Frappe evaluation environment for Omni v4.

The goal is to prove the selective adoption plan before building the long-term `omni_operations` app.

Related docs:

- `../docs/32_erpnext_selective_adoption_plan.md`
- `../docs/33_omniv4_execution_backlog.md`

## Current Decision

Use ERPNext/Frappe `version-15` for evaluation.

Do not use `/Users/h2o/erpnext-develop` as the runtime yet. That checkout is useful for source review, but it appears to be a develop branch and may require a newer runtime.

## Current Local Evaluation Site

Created on 2026-08-16:

- Frappe Docker repo: `erpnext-eval/frappe_docker`
- Docker compose project: `omni-erpnext-eval`
- Bench path inside the repo: `erpnext-eval/frappe_docker/development/frappe-bench`
- Site: `development.localhost`
- Administrator password: `admin`
- Installed apps:
  - Frappe `15.118.0` on `version-15`
  - ERPNext `15.119.2` on `version-15`

Useful commands from `erpnext-eval/frappe_docker`:

```bash
docker compose -f devcontainer-example/docker-compose.yml -p omni-erpnext-eval ps
docker compose -f devcontainer-example/docker-compose.yml -p omni-erpnext-eval exec -T frappe bash -lc 'cd /workspace/development/frappe-bench && bench --site development.localhost list-apps'
docker compose -f devcontainer-example/docker-compose.yml -p omni-erpnext-eval exec -T frappe bash -lc 'cd /workspace/development/frappe-bench && bench --site development.localhost doctor'
```

Runtime notes:

- The Frappe bench image includes Python `3.12.12` and `3.14.2`; use Python `3.12.12` for the version-15 bench.
- MariaDB is currently `11.8`; Frappe v15 warns that this is newer than the tested range. Keep it for disposable evaluation only and pin a tested MariaDB version before any production design.
- The scheduler and workers are not active until the development bench is started.

## Why Docker First

This Mac currently does not have:

- `bench`
- Homebrew
- pyenv
- uv
- pipx
- MariaDB/MySQL
- Redis

Docker is installed, so a containerized evaluation environment is the cleanest first path once Docker Desktop is running.

## Evaluation Targets

The evaluation site must prove these ERPNext flows:

1. Company setup for a Zimbabwe operating company.
2. Customer creation.
3. Supplier creation.
4. Item creation for:
   - Fleet monitoring service
   - Tracker hardware
   - SIM card
   - Installation labour
   - Maintenance labour
   - Fleet parts
5. Warehouse creation for:
   - Main stock
   - Technician stock
   - Faulty/returns stock
6. Quotation to Sales Order to Sales Invoice.
7. Payment Entry against invoice.
8. Purchase Order to Purchase Receipt to Purchase Invoice.
9. Asset record for a vehicle or tracker.
10. Support/Issue record.

Only after these are proven should we scaffold `omni_operations`.

## First Omni Custom App Target

Once bench is ready, create:

```text
omni_operations
```

Initial Omni DocTypes:

- Fleet Vehicle
- Tracker Profile
- SIM Profile
- Wialon Account
- Wialon Unit Link
- Wialon Sync Log
- Customer Fleet Profile

## Manual Startup Notes

If Docker Desktop is not running, start it first.

Check Docker:

```bash
docker ps
```

If Docker is running, use the official Frappe Docker development setup or a local bench setup to create an ERPNext `version-15` site. The disposable demo image is useful for first inspection, but custom app development requires a bench/dev setup that can install `omni_operations`.

## Acceptance Criteria for A-004

`A-004` is done when:

- A local Frappe bench or Docker-based bench exists.
- ERPNext `version-15` can be installed.
- A site can start locally.
- We can access Desk in the browser.
- We can later install a custom app into the same environment.
