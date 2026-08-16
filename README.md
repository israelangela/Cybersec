# CyberSec

CyberSec is a Cyber Threat Intelligence platform rebuilt from a small, working
foundation. The project is intentionally phase-based: each phase must remain
executable, testable, documented and maintainable before the next phase begins.

## Current Status

Phase 2 - Intelligence Collection is implemented.

Included so far:

- PostgreSQL with Docker Compose
- FastAPI backend
- SQLAlchemy 2.x async database access
- Alembic migrations
- Initial `User`, `Source` and `Item` schema
- Structured logging
- `GET /health`
- `GET /ready`
- Source management API
- Source management UI
- RSS intelligence collection
- Manual collection endpoints
- Basic scheduler configuration
- Item listing API and UI
- Next.js frontend in professional dark mode
- Backend tests, frontend checks and project documentation

Not included yet:

- Normalization
- AI enrichment
- RAG
- Reports
- Alerts
- Authentication and RBAC

## Requirements

- Docker Desktop
- Docker Compose v2
- GitHub CLI, only when publishing to GitHub

The backend runs in Docker with Python 3.13, so host Python is not required.

## Quick Start

```powershell
cd C:\Users\lasrosasdm\Documents\Desarrollo\Cybersec
docker compose up -d --build
docker compose run --rm backend alembic upgrade head
```

Open:

- Frontend: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- Readiness: `http://localhost:8000/ready`
- Sources API: `http://localhost:8000/sources`
- Items API: `http://localhost:8000/items`
- Collection run: `POST http://localhost:8000/collection/run`

## Services

| Service | URL | Purpose |
| --- | --- | --- |
| `frontend` | `http://localhost:3000` | Next.js interface |
| `backend` | `http://localhost:8000` | FastAPI API |
| `postgres` | `localhost:5432` | PostgreSQL database |

## Local Database

Default development connection:

- Host: `localhost`
- Port: `5432`
- Database: `cybersec`
- User: `cybersec`
- Password: see `.env.example`

The repository must not contain real secrets. Use `.env` locally and keep it
untracked.

## Validation

```powershell
docker compose config --quiet
docker compose build
docker compose run --rm backend ruff check .
docker compose run --rm backend pytest
docker compose run --rm frontend npm audit --audit-level=high
docker compose run --rm frontend npm run typecheck
docker compose run --rm frontend npm run lint
docker compose run --rm frontend npm run build
```

## Documentation

- [Architecture](ARCHITECTURE.md)
- [Roadmap](ROADMAP.md)
- [Security](SECURITY.md)
- [Development Guide](DEVELOPMENT.md)
- [API Reference](API.md)
- [Database Schema](DATABASE.md)

## Phase Boundary

Next recommended step: Phase 3 - Normalization.

Do not begin Phase 3 until explicitly requested.
