# Migration Validation Checklist

This document captures the steps needed to validate backend Alembic migrations after introducing the hardware inventory tables.

## Prerequisites

- Docker Desktop (or any Docker daemon) running locally.
- Python virtual environment with project dependencies installed (`pip install -r backend/requirements.txt`).
- `.env` configured with `DATABASE_URL=postgresql://omni_user:omni_password@127.0.0.1:15432/omni_logistics`.

## Steps

1. **Start the database**

   - Ensure the Docker daemon is running, then bring up Postgres only:
     ```bash
     docker compose up -d postgres
     ```
   - The container executes `migrations/init.sql`, which now guarantees the `omni_user` role, `omni_logistics` database, and grants.

2. **Run migrations**

   - Activate the backend virtual environment and execute:
     ```bash
     cd backend
     alembic upgrade head
     ```
   - Successful runs create the `hardware_inventory` and `hardware_assignments` tables along with their enums and indexes.

3. **Smoke check**
   - Optional: connect via psql to verify the new tables/enums:
     ```bash
     psql postgresql://omni_user:omni_password@127.0.0.1:15432/omni_logistics \
       -c "\d hardware_inventory" \
       -c "\d hardware_assignments"
     ```

## Current Status

- `docker compose up -d postgres` succeeds and exposes Postgres on host port `15432`.
- `alembic upgrade head` completes successfully (current head: `5a6f1d2d3c1b`).
