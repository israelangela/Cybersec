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
- `api/routes.py`: Phase 0 system endpoints
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
- `app/page.tsx`: Phase 0 status screen
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

CyberSec is built phase by phase. Phase 1 is complete only as source
management. Phase 2 must focus on intelligence collection and must not introduce
AI, RAG, reports or alerts unless explicitly requested later.
