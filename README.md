# CyberSec

CyberSec is a Cyber Threat Intelligence platform rebuilt from a small, working
foundation. The project is intentionally phase-based: each phase must remain
executable, testable, documented and maintainable before the next phase begins.

## Current Status

Phase 8 - War Room is implemented.

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
- Text normalization pipeline
- HTML-to-text extraction for collected items
- Heuristic language detection
- Normalized SHA-256 hashing
- Duplicate marking based on normalized content
- Manual normalization endpoints and UI action
- Intelligence workbench UI
- Item search, source, status, language and duplicate filters
- Intelligence summary metrics
- Item detail panel with normalized content and source metadata
- Item statistics API
- AI enrichment API using OpenRouter-compatible chat completions
- AI summary, severity, confidence, tags, CVEs, IOCs, MITRE techniques and actions
- Enrichment workbench actions for selected items and small batches
- Cyber intelligence entity extraction from enriched items
- CVE, IOC, MITRE, tag and threat actor entity indexing
- Risk scoring for extracted cyber entities
- Intelligence synchronization endpoints and workbench panel
- pgvector-enabled PostgreSQL runtime
- Deterministic local embeddings for enriched intelligence
- Story clustering over enriched items and cyber entities
- Story synchronization endpoints and workbench panel
- Cyber War Room operational snapshot API
- War Room UI with operating mode, risk queue, entity pulse, timeline and source health
- Next.js frontend in professional dark mode
- Backend tests, frontend checks and project documentation

Not included yet:

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
- Normalization run: `POST http://localhost:8000/normalization/run`
- Item stats: `GET http://localhost:8000/items/stats`
- Enrichment run: `POST http://localhost:8000/enrichment/run`
- Item enrichment: `POST http://localhost:8000/enrichment/items/{item_id}/run`
- Intelligence sync: `POST http://localhost:8000/intelligence/sync`
- Intelligence stats: `GET http://localhost:8000/intelligence/stats`
- Cyber entities: `GET http://localhost:8000/intelligence/entities`
- Stories sync: `POST http://localhost:8000/stories/sync`
- Stories stats: `GET http://localhost:8000/stories/stats`
- Stories API: `GET http://localhost:8000/stories`
- War Room: `GET http://localhost:8000/war-room`

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

AI enrichment requires `OPENROUTER_API_KEY` in the local environment. The safe
template in `.env.example` documents the variable names without storing a real
key.

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

Next recommended step: Phase 9 - RAG / Ask CyberSec / citations.

Do not begin Phase 9 until explicitly requested.
