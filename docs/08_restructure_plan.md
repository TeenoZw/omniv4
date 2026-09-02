# 08 – Restructure Plan

This plan reflects the new Omni Logistics focus: enquiry intake, billing, onboarding, and Wialon-based tracking access. It enumerates the refactors needed to keep modules and documentation aligned.

## Goals

1. **Active scope only** – keep `backend`, `admin-web`, `client-web`, and `docs` as the active workspace.
2. **Archive legacy systems** – move deprecated services and infra into `archive/` with clear notes.
3. **Onboarding-first UX** – ensure landing and admin flows match the enquiry → quote → activation path.
4. **Documentation parity** – update docs to reflect the new scope and archive legacy references.

## Workstreams & Tasks

### 1. Documentation Cleanup

- Update `docs/01_overview.md`, `docs/06_roadmap.md`, and `docs/11_restructure_summary.md`.
- Move legacy telemetry references to `archive/docs-legacy/`.

### 2. Backend (FastAPI)

- Enquiry capture endpoints with admin updates.
- Billing + subscription lifecycle models.
- Customer portal auth + RBAC.

### 3. Admin Web (Svelte)

- Enquiry dashboard (quote, status updates).
- Hub provisioning and subscription metadata.

### 4. Client Web (Svelte)

- Landing page with enquiry form (no hardware pricing).
- Customer portal login for billing/support.
- Tracking handoff to Wialon.

### 5. Infrastructure & Ops

- Keep deployment steps focused on backend/admin/client only.
- Archive telemetry and ingestion services.

## Acceptance Criteria

- Only the active modules remain at the repo root.
- Legacy services live under `archive/` with a clear README.
- Docs and UX reference Wialon for tracking, Omni for onboarding/billing.

## Reporting & Tracking

- Maintain status in `docs/06_roadmap.md`.
- Track blockers in the project tracker.
