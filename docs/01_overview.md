# 01 – Project Overview

This document synthesizes the Omni Logistics development guide and the Phase Roadmap (`docs/06_roadmap.md`) into a single orientation reference for new collaborators. It focuses on the active codebase that lives under the `backend`, `admin-web`, `client-web`, and `docs` directories.

## Vision

Build a fleet management ecosystem that delivers:

- Real-time GPS tracking through Wialon with operational support in Omni
- FastAPI-powered REST/WebSocket APIs with JWT + RBAC enforcement
- Svelte admin/client portals for onboarding, billing, and support
- Plan-aware subscription workflows (Individual, Business, add-ons)
- Integration handoff to Wialon for tracking access

## Active Workspace

```
omniv3/
├── backend/        # FastAPI API + auth + billing + enquiries
├── admin-web/      # Svelte admin dashboards
├── client-web/     # Svelte customer portal + landing
└── docs/           # Primary documentation set
```

Archived modules live under `archive/` and are no longer part of the active build.

## Guiding Principles

1. **Customer onboarding first** – onboarding, billing, and support must be reliable before expansion.
2. **Async everywhere** – ingestion workers, FastAPI endpoints, and Redis bridges remain fully async.
3. **Role-based security** – JWT tokens + RBAC guard every API and socket.
4. **Plan-aware UX** – subscription details are surfaced consistently across admin and client portals.
5. **Documentation parity** – every architectural decision is captured in the numbered docs within `/docs`.

## Documentation Map

| Doc                       | Purpose                                        |
| ------------------------- | ---------------------------------------------- |
| `docs/01_overview.md`     | This high-level guide                          |
| `docs/02_architecture.md` | Detailed service architecture and data flow    |
| `docs/03_api.md`          | REST/WebSocket surface area                    |
| `docs/04_schema.md`       | TimescaleDB + ORM reference                    |
| `docs/05_deployment.md`   | DigitalOcean + Docker workflows                |
| `docs/06_roadmap.md`      | Phase-by-phase execution plan                  |
| `docs/07_contributing.md` | Collaboration, coding standards, review policy |

## Active Deliverables

- Deliver the enquiry → quote → onboarding flow with admin follow-up.
- Implement subscription enforcement + billing management per `docs/06_roadmap.md`.
- Maintain deployment readiness for the shared portal infrastructure.

## Contacts & References

- Developer Implementation Guide (internal) – informs module responsibilities.
- `docs/06_roadmap.md` – single source for status tracking.
- `docs/11_restructure_summary.md` – describes current repository cleanup.
- `docs/10_implementation_checklist.md` – granular task tracking.
