# 11 – Restructure Summary

## Overview

- Repository realigned with the new Omni Logistics onboarding + billing focus.
- Active scope: `backend`, `admin-web`, `client-web`, `docs`.
- Legacy services and infrastructure have been moved under `archive/`.

## Clean Repository Layout

```
omniv3/
├── backend/          # FastAPI API, migrations, services
├── admin-web/        # Svelte admin dashboard
├── client-web/       # Svelte customer portal + landing
├── docs/             # Architecture + API specs
└── archive/          # Archived legacy services and infra
```

## Key Components Implemented

### 1. Backend API (`backend/app/`)

- FastAPI routers for users, hubs, subscriptions, enquiries, and billing workflows.
- JWT auth with refresh tokens and role-based guards.
- Service layer abstractions encapsulate business rules cleanly.

### 2. Frontend & Admin Shells

- Admin Svelte app for enquiries, hub provisioning, and subscription management.
- Client Svelte app for landing + customer portal access.
- Shared UX patterns aligned with onboarding → quote → activation flow.

### 3. Documentation Set

- `docs/11_restructure_summary.md` (this file).
- `docs/10_implementation_checklist.md` (deliverables + next steps).
- `docs/09_quickstart.md` (local bring-up guide for active modules).
- Legacy telemetry and ingestion references archived under `archive/docs-legacy/`.

## File Inventory

| Category      | Files                                                                 |
| ------------- | --------------------------------------------------------------------- |
| Backend       | FastAPI routers, services, auth, migrations                           |
| Admin web     | Enquiry dashboard, hub management, onboarding workflows               |
| Client web    | Landing, enquiry form, customer login                                 |
| Documentation | `docs/` with current scope + archived legacy references in `archive/` |

## Deployment Reference

| Scenario      | Command(s)                         |
| ------------- | ---------------------------------- |
| Backend tests | `cd backend && pytest`             |
| Admin dev     | `cd admin-web && npm run dev`      |
| Client dev    | `cd client-web && npm run dev`     |

## Current Status

| Area              | Completion |
| ----------------- | ---------- |
| Onboarding flow   | 70%        |
| Admin dashboard   | 60%        |
| Client landing    | 80%        |
| Documentation     | 60%        |

## Quick Command Cheat Sheet

```bash
cd backend && pytest
cd admin-web && npm run dev
cd client-web && npm run dev
```

## Environment Endpoints

- Backend API: `http://localhost:8000/docs`
- Admin web: `http://localhost:5173`
- Client web: `http://localhost:5174`

---

**Version:** 3.0.0  
**Date:** February 4, 2026  
**Author:** Omni Logistics Engineering
