# Omni Logistics – Copilot Development Guide

This document provides structured instructions for developing the Omni Logistics fleet management ecosystem using GitHub Copilot.

## Project Context

**Project Name:** Omni Logistics  
**Type:** Multi-root, multi-technology fleet management platform  
**Status:** Development in Progress

### Key Requirements

- Multi-root VSCode workspace (backend, telemetry, admin-web, client-web, mobile, shared, docs)
- Backend: Python FastAPI with PostgreSQL/TimescaleDB
- Telemetry: Python MQTT parser
- Frontend: Svelte dashboards with Tailwind CSS
- Mobile: React Native (Expo)
- Authentication: JWT with role-based access
- Subscription tiers: Basic, Pro, Enterprise
- Real-time alerts via WebSocket/MQTT

## Development Checklist

- [x] Clarify Project Requirements
- [x] Create Multi-Root Workspace Structure
- [ ] Setup Backend (FastAPI)
- [ ] Setup Telemetry Parser (Python/MQTT)
- [ ] Setup Admin Web Dashboard (Svelte)
- [ ] Setup Client Web Portal (Svelte)
- [ ] Setup Mobile App (React Native)
- [ ] Configure Shared Utilities
- [ ] Setup Database Schema & Migrations
- [ ] Implement Authentication & Authorization
- [ ] Implement Subscription Tier Logic
- [ ] Build Real-time Alert System
- [ ] Create API Documentation (Swagger)
- [ ] Setup Docker & Docker Compose
- [ ] Write Unit & Integration Tests
- [ ] Create CI/CD Pipelines
- [ ] Deploy to Cloud Infrastructure
- [ ] Complete Project Documentation

## Module-Specific Guidelines

### Backend Module (`/backend`)

**Technology:** Python FastAPI, PostgreSQL, SQLAlchemy ORM  
**Key Tasks:**

- Initialize FastAPI project structure
- Define Pydantic models for API schemas
- Create SQLAlchemy models for database
- Implement JWT authentication middleware
- Build CRUD endpoints for core entities
- Add role-based access control (RBAC)
- Implement subscription tier validation
- Create real-time alert endpoints
- Add WebSocket support for live updates
- Write comprehensive API tests

**Dependencies:** `fastapi`, `sqlalchemy`, `pydantic`, `python-jose`, `passlib`, `psycopg2`

### Telemetry Module (`/telemetry`)

**Technology:** Python, paho-mqtt, TimescaleDB  
**Key Tasks:**

- Setup MQTT client with error handling
- Implement JSON payload parser
- Define telemetry data schema
- Create database insert logic
- Add data validation
- Implement logging and monitoring
- Write unit tests for parser
- Handle connection retries

**Dependencies:** `paho-mqtt`, `psycopg2`, `python-dotenv`, `pydantic`

### Admin Web Module (`/admin-web`)

**Technology:** Svelte, Tailwind CSS, SvelteKit  
**Key Tasks:**

- Setup SvelteKit project
- Create authentication pages
- Build device inventory UI
- Create hub management interface
- Build technician workflow screens
- Implement audit log viewer
- Add responsive design
- Write component tests
- Setup API integration

**Dependencies:** `svelte`, `sveltekit`, `tailwindcss`, `axios`

### Client Web Module (`/client-web`)

**Technology:** Svelte, Tailwind CSS, SvelteKit  
**Key Tasks:**

- Setup SvelteKit project
- Create real-time map component (Leaflet/Mapbox)
- Build trip playback UI
- Implement trip filtering
- Create alerts dashboard
- Build reports section (tier-based)
- Add responsive design
- Implement feature restriction logic

**Dependencies:** `svelte`, `sveltekit`, `tailwindcss`, `leaflet`, `axios`

### Mobile Module (`/mobile`)

**Technology:** React Native, Expo  
**Key Tasks:**

- Initialize Expo project
- Setup navigation (React Navigation)
- Create authentication screens
- Build vehicle tracking screen
- Implement trip playback
- Add push notifications setup
- Implement offline caching (AsyncStorage)
- Add permission handling
- Write mobile-specific tests

**Dependencies:** `expo`, `react-native`, `react-navigation`, `expo-notifications`

### Shared Module (`/shared`)

**Purpose:** Centralized constants, enums, and utilities  
**Content:**

- Subscription tier definitions
- Role definitions and permissions
- Common error codes
- Alert type enums
- Validation utilities
- API response structures

## Code Standards & Best Practices

### Python (Backend & Telemetry)

- Follow PEP 8 style guide
- Use type hints throughout
- Write docstrings for functions/classes
- Organize imports (stdlib, third-party, local)
- Use logging instead of print statements
- Implement proper error handling

### JavaScript/Svelte (Frontend)

- Use ESM modules
- Follow Prettier formatting
- Add JSDoc comments
- Use semantic HTML
- Implement accessibility (a11y)
- Test components with Vitest/Jest

### General

- Write descriptive commit messages
- Create feature branches for all work
- Keep functions small and focused
- DRY principle – avoid repetition
- Write tests alongside features
- Document complex logic

## Testing Strategy

**Backend:**

- Unit tests for models, services, utilities
- Integration tests for API endpoints
- Tests for authentication/authorization
- Database transaction tests

**Telemetry:**

- Unit tests for payload parsing
- Tests for data validation
- Mock MQTT broker tests
- Error handling tests

**Frontend:**

- Component unit tests
- Integration tests for pages
- E2E tests for critical flows
- Accessibility tests

**Coverage:** Aim for 80%+ coverage

## Database Guidelines

### Schema Design

- Use UUID for primary keys (except junction tables)
- Add created_at/updated_at timestamps
- Use CHECK constraints for enums
- Index foreign keys
- Partition telemetry table by time (TimescaleDB hypertable)

### Migrations

- Use Alembic for schema versioning
- Write both up and down migrations
- Test migrations on realistic data
- Keep migrations atomic

## API Design

### RESTful Conventions

- `GET /resource` – List
- `POST /resource` – Create
- `GET /resource/:id` – Read
- `PUT /resource/:id` – Update
- `DELETE /resource/:id` – Delete

### Response Format

```json
{
  "success": true,
  "data": {},
  "error": null,
  "timestamp": "2025-11-17T10:00:00Z"
}
```

### Error Handling

- Use appropriate HTTP status codes
- Include error messages and codes
- Log errors server-side
- Avoid exposing internal details

## Security Checklist

- [ ] All passwords hashed (bcrypt)
- [ ] JWT tokens with expiration
- [ ] HTTPS enforced in production
- [ ] CORS configured properly
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (ORM)
- [ ] Rate limiting implemented
- [ ] Secrets in environment variables
- [ ] API keys for device authentication
- [ ] Audit logs for sensitive operations

## Deployment Checklist

- [ ] Docker images for each service
- [ ] Docker Compose for local development
- [ ] Environment configuration files
- [ ] Database backup strategy
- [ ] Monitoring and logging setup
- [ ] Health check endpoints
- [ ] Load testing complete
- [ ] Security audit passed
- [ ] Documentation finalized
- [ ] Runbook for operations

## Common Development Tasks

### Adding a New API Endpoint

1. Define request/response Pydantic models
2. Add database model if needed
3. Implement service logic
4. Create route handler
5. Add authentication/authorization
6. Write tests
7. Document in Swagger

### Adding a New Database Table

1. Create SQLAlchemy model
2. Write Alembic migration
3. Test migration
4. Update API endpoints
5. Update tests

### Adding a New Feature to Frontend

1. Create component structure
2. Add route if page-level
3. Implement API integration
4. Add styling with Tailwind
5. Write component tests
6. Add to navigation

## Useful Commands

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
pytest
```

**Frontend:**

```bash
cd admin-web
npm install
npm run dev
npm test
```

**Database:**

```bash
alembic upgrade head
alembic downgrade -1
```

**Docker:**

```bash
docker-compose up
docker-compose down
docker-compose logs -f service-name
```

## Communication with Copilot

### Effective Queries

- Specify file paths and line numbers
- Include relevant code context
- Ask for specific implementation details
- Request tests alongside code

### Example Good Query

> "In `/backend/app/models.py`, add a `Trip` model with fields: id (UUID primary key), vehicle_id (FK to Vehicle), start_time, end_time, distance_km, duration_minutes. Include timestamps and proper SQLAlchemy relationships."

## Project Phases Timeline

1. **Phase 1** (Week 1-2): Telemetry & data ingestion
2. **Phase 2** (Week 2-3): Backend API core
3. **Phase 3** (Week 3-4): Admin dashboard
4. **Phase 4** (Week 4-5): Client portal
5. **Phase 5** (Week 5-6): Mobile app
6. **Phase 6** (Week 6-7): Subscription logic
7. **Phase 7** (Week 7-8): Alerts & notifications
8. **Phase 8** (Week 8-9): Deployment
9. **Phase 9** (Week 9-10): Testing & QA
10. **Phase 10** (Week 10-11): Documentation

## Key Contacts & Resources

- **Architecture Docs:** `/docs/architecture.md`
- **API Specification:** `/docs/api-spec.yaml`
- **Database Schema:** `/docs/db-schema.md`
- **Contributing Guide:** `/docs/CONTRIBUTING.md`

---

**Last Updated:** November 17, 2025  
**Maintained By:** Development Team
