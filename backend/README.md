"""Backend README."""

# Omni Logistics Backend API

FastAPI-based REST API for Omni Logistics onboarding, billing, and support workflows.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Environment Variables

Create `.env` file:

```
DATABASE_URL=postgresql://omni_user:omni_password@127.0.0.1:15432/omni_logistics
SECRET_KEY=your-secret-key
ENVIRONMENT=production
DEBUG=False
AUTO_CREATE_SCHEMA=False

```

## Running

```bash
uvicorn main:app --reload
```

Access API docs: http://localhost:8000/docs

Optional Postgres setup:

```bash
docker compose -f ../docker-compose.yml up -d postgres
```
Run migrations:

```bash
python -m alembic upgrade head
```

## Project Structure

- `app/` - Main application code
  - `models/` - SQLAlchemy models
  - `schemas/` - Pydantic request/response schemas
  - `api/routes/` - API endpoints
  - `core/` - Configuration, security, database
  - `services/` - Business logic
- `migrations/` - Alembic database migrations
- `tests/` - Test suite
