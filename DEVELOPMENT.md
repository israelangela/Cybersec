# Development Guide

## Local Workflow

Start the stack:

```powershell
docker compose up -d --build
```

Apply migrations:

```powershell
docker compose run --rm backend alembic upgrade head
```

Stop the stack:

```powershell
docker compose down
```

Stop the stack and remove the development database volume:

```powershell
docker compose down -v
```

## Backend

The backend is a FastAPI application packaged under `backend/src/cybersec_api`.

Important modules:

- `main.py`: FastAPI app setup
- `api/routes.py`: API router composition
- `core/config.py`: typed settings
- `core/logging.py`: structured logging
- `db/session.py`: async SQLAlchemy engine and session dependency
- `models/`: SQLAlchemy ORM models
- `alembic/`: database migrations

Run backend checks:

```powershell
docker compose run --rm backend ruff check .
docker compose run --rm backend pytest
```

## Frontend

The frontend is a Next.js App Router application in `frontend/`.

Important files:

- `app/layout.tsx`: root layout and metadata
- `app/page.tsx`: operational dashboard shell
- `app/globals.css`: dark visual foundation
- `lib/system-status.ts`: backend health integration

Run frontend checks:

```powershell
docker compose run --rm frontend npm audit --audit-level=high
docker compose run --rm frontend npm run typecheck
docker compose run --rm frontend npm run lint
docker compose run --rm frontend npm run build
```

## Migrations

All database schema changes must use Alembic.

Create a migration after model changes:

```powershell
docker compose run --rm backend alembic revision --autogenerate -m "describe change"
```

Apply migrations:

```powershell
docker compose run --rm backend alembic upgrade head
```

## Phase Discipline

CyberSec is built phase by phase. Phase 6 is complete as a derived cyber
intelligence layer over enriched items. Phase 7 must focus on stories,
embeddings, pgvector and clustering, and must not introduce RAG, reports or
alerts unless explicitly requested later.

## AI Enrichment

Set `OPENROUTER_API_KEY` locally before running live enrichment. Keep real keys
out of commits and logs.

## Cyber Intelligence

Run AI enrichment before synchronizing cyber entities:

```powershell
docker compose run --rm backend alembic upgrade head
Invoke-RestMethod -Method Post "http://localhost:8000/enrichment/run?limit=10"
Invoke-RestMethod -Method Post "http://localhost:8000/intelligence/sync?limit=500"
```

Cyber intelligence sync is deterministic and does not call the AI provider. It
rebuilds derived entities for completed enrichments inside the configured limit.
