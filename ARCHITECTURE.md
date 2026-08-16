# CyberSec Architecture

## Current phase

Phase 1 - Source Management.

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
- `cybersec_api.api.routes`: API router composition
- `cybersec_api.api.system`: health and readiness routes
- `cybersec_api.api.sources`: source management routes
- `cybersec_api.core.config`: pydantic-settings configuration
- `cybersec_api.core.logging`: structlog configuration
- `cybersec_api.db.session`: async SQLAlchemy engine/session
- `cybersec_api.models`: initial ORM schema
- `cybersec_api.schemas`: Pydantic API contracts
- `cybersec_api.crud`: persistence helpers

## Database

PostgreSQL is the source of truth. Alembic owns schema evolution.

Initial tables:

- `users`
- `sources`
- `items`

Future phases may add enrichments, stories, reports, departments, watchlists, audit logs, alerts and model usage.

## Source Management

Phase 1 adds CRUD operations for intelligence sources. The system stores source
metadata and configuration only. It does not fetch, parse or normalize source
content yet.

Supported source types:

- `rss`
- `web`
- `api`
- `other`

## Frontend

The frontend is a Next.js App Router application with TypeScript and Tailwind
CSS. Phase 1 exposes an operational source management dashboard.

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

Phase 1 exposes source mutation endpoints but does not fetch remote content.
External source URLs are stored as untrusted input. The `users` table exists so
authentication and RBAC can be added later without reshaping the foundation.

## Future direction

The architecture is intentionally simple and AWS-ready without adding AWS dependencies prematurely.
