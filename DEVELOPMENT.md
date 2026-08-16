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

CyberSec is built phase by phase. Phase 8 is complete as a Cyber War Room
experience over stories, entities, enriched items and source health. Phase 9
must focus on RAG, Ask CyberSec and citations only when explicitly requested.

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

## Story Clustering

Run enrichment and cyber intelligence sync before synchronizing stories:

```powershell
docker compose run --rm backend alembic upgrade head
Invoke-RestMethod -Method Post "http://localhost:8000/enrichment/run?limit=10"
Invoke-RestMethod -Method Post "http://localhost:8000/intelligence/sync?limit=500"
Invoke-RestMethod -Method Post "http://localhost:8000/stories/sync?limit=500"
```

Story sync is deterministic and does not call the AI provider. It generates
local hashed embeddings, combines text similarity with shared cyber entities and
rebuilds the current story clusters.

The PostgreSQL service uses `pgvector/pgvector:pg18`. If an existing local
database volume was created with the plain PostgreSQL image and PostgreSQL emits
a collation mismatch warning after switching images, run:

```powershell
docker compose exec postgres psql -U cybersec -d cybersec -c "REINDEX DATABASE cybersec;"
docker compose exec postgres psql -U cybersec -d cybersec -c "ALTER DATABASE cybersec REFRESH COLLATION VERSION;"
```

## War Room

The War Room is a read-only operational snapshot. Run collection,
normalization, enrichment, intelligence sync and story sync first to populate the
underlying analytical layers:

```powershell
Invoke-RestMethod "http://localhost:8000/war-room?limit=10"
```

The endpoint does not create reports, alerts, cases or RAG answers.
