# CyberSec Architecture

## Current phase

Phase 0 - Foundation.

## Monorepo layout

```text
Cybersec/
  backend/     FastAPI application, SQLAlchemy models, Alembic migrations
  frontend/    Next.js application
  docker-compose.yml
```

## Backend

The backend uses FastAPI with a small `src` package layout:

- `cybersec_api.main`: app factory and middleware setup
- `cybersec_api.api.routes`: health and readiness routes
- `cybersec_api.core.config`: pydantic-settings configuration
- `cybersec_api.core.logging`: structlog configuration
- `cybersec_api.db.session`: async SQLAlchemy engine/session
- `cybersec_api.models`: initial ORM schema

## Database

PostgreSQL is the source of truth. Alembic owns schema evolution.

Initial tables:

- `users`
- `sources`
- `items`

Future phases may add enrichments, stories, reports, departments, watchlists, audit logs, alerts and model usage.

## Frontend

The frontend is a Next.js App Router application with TypeScript and Tailwind CSS. Phase 0 exposes a professional dark status screen only.

## Runtime

Docker Compose runs:

- `postgres`
- `backend`
- `frontend`

Readiness depends on a successful database `SELECT 1`.

## Configuration

Configuration is read from environment variables through `pydantic-settings`.
The `.env.example` file documents development defaults, but real `.env` files
must remain untracked.

## Observability Foundation

Phase 0 configures structured JSON logging with `structlog`. Request IDs,
correlation IDs, metrics and OpenTelemetry are planned for future phases.

## Security Boundary

Phase 0 does not expose user-facing mutation endpoints. The `users` table exists
so authentication and RBAC can be added later without reshaping the foundation.

## Future direction

The architecture is intentionally simple and AWS-ready without adding AWS dependencies prematurely.
