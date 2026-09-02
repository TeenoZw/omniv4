# Omni v4

Omni v4 is the next Omni Logistics business platform.

The current product direction is:

- Frappe/ERPNext for the internal admin, accounting, operations, inventory, permissions, and workflow backbone.
- `omni_operations` as the custom Frappe app for fleet, trackers, SIMs, telematics, maintenance, customer operations, fiscalisation, and Omni-specific workflows.
- `client-web` as the Svelte public website and customer portal experience.
- Legacy v3 code retained as reference and migration source only.

## Active Architecture

| Area | Active implementation | Purpose |
| --- | --- | --- |
| Admin app | `erpnext-eval/frappe_docker/development/frappe-bench/apps/omni_operations` | Omni-focused Frappe/ERPNext Desk for directors and staff. |
| Public website | `client-web` | Branded public website for `www.omnilogistics.co.zw`. |
| Customer portal | `client-web` | Customer-facing portal for vehicles, trackers, invoices, documents, and support. |
| ERP backbone | ERPNext in the Frappe bench | Customers, suppliers, invoices, payments, items, warehouses, accounting, and reports. |
| Migration tooling | `migration_exports`, `migration_working`, `scripts` | v3 export transformation, validation, and Omni v4 import support. |

## Legacy Reference Areas

These folders belong to the previous v3 architecture and should not receive new v4 product features unless the architecture is deliberately changed:

- `backend` - old FastAPI backend.
- `admin-web` - old custom admin dashboard.
- older docs that describe FastAPI/PostgreSQL as the active production backend.

Use them for:

- migration reference
- old UI reference
- data model comparison
- historical behavior checks

## Target Domains

Production should be split by responsibility:

- `www.omnilogistics.co.zw` - public Svelte website
- `www.omnilogistics.co.zw/portal` or `portal.omnilogistics.co.zw` - Svelte customer portal
- `admin.omnilogistics.co.zw` - Frappe/ERPNext admin app

The Frappe website routes should remain fallback/admin-support routes, not the primary public website.

## Local Development

Start the Svelte public website and customer portal:

```bash
docker compose -f docker-compose.omniv4-surfaces.yml up --build
```

Default local URLs:

- public website: `http://localhost:5174`
- customer portal: `http://localhost:5175/portal`

Run Svelte checks:

```bash
cd client-web
npm run check
```

The Frappe/ERPNext evaluation bench lives under:

```text
erpnext-eval/frappe_docker/development/frappe-bench
```

Useful Frappe commands are captured in:

- `erpnext-eval/README.md`
- `docs/42_omniv4_developer_runbook.md`

## Key Planning Docs

- `docs/31_omniv4_work_plan.md` - full Omni v4 product plan
- `docs/32_erpnext_selective_adoption_plan.md` - what ERPNext owns versus what Omni customizes
- `docs/33_omniv4_execution_backlog.md` - detailed historical execution backlog
- `docs/38_omniv4_production_readiness.md` - production readiness gaps
- `docs/39_zimra_fdms_api_execution_plan.md` - ZIMRA fiscalisation plan
- `docs/40_omniv4_consolidation_execution_plan.md` - current consolidation plan
- `docs/42_omniv4_developer_runbook.md` - local development and verification commands
- `docs/45_render_staging_runbook.md` - Render staging plan for the Frappe/ERPNext admin app

## Current Development Priority

1. Consolidate documentation and architecture around Omni v4.
2. Finalize the public/admin/customer deployment split.
3. Build narrow Frappe APIs for the Svelte customer portal.
4. Wire the Svelte portal to those APIs.
5. Focus Frappe Desk around Omni operations.
6. Rehearse the final v3 migration from a fresh Supabase export.
7. Validate real telematics and ZIMRA production flows.
8. Harden deployment, backups, monitoring, and permissions.

## Development Rule

Build Omni-specific workflows on top of ERPNext's reliable business engine.

Do not duplicate accounting, customers, invoices, items, warehouses, or payments unless there is a clear reason ERPNext cannot serve the requirement.
