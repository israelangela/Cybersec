# CyberSec Architecture

## Current phase

Phase 5 - AI Enrichment.

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
- `cybersec_api.api.collection`: manual collection routes
- `cybersec_api.api.enrichment`: manual AI enrichment routes
- `cybersec_api.api.normalization`: manual normalization routes
- `cybersec_api.api.items`: collected item routes
- `cybersec_api.collectors`: RSS collection and scheduler logic
- `cybersec_api.enrichment`: OpenRouter client and enrichment orchestration
- `cybersec_api.normalizers`: text extraction, language detection and duplicate marking
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

## Intelligence Collection

Phase 2 adds RSS collection. The collector downloads enabled RSS sources,
parses feed entries, creates raw `items` and avoids duplicates by checking URL,
content hash and source-specific external ID.

Collection updates source health fields:

- `last_fetched_at`
- `last_error`
- `error_count`

The scheduler uses APScheduler and is disabled by default. Enable it with
`COLLECTOR_SCHEDULER_ENABLED=true`.

## Normalization

Phase 3 converts collected raw items into a normalized representation. The
normalizer extracts readable text from HTML, collapses whitespace, detects a
simple language code, computes a normalized SHA-256 hash and marks duplicates
without deleting the original record.

Normalization writes these item fields:

- `normalized_title`
- `normalized_content`
- `normalized_hash`
- `language`
- `is_duplicate`
- `duplicate_of_item_id`
- `normalization_error`
- `normalized_at`

## Frontend

The frontend is a Next.js App Router application with TypeScript and Tailwind
CSS. Phase 4 exposes source management, manual RSS collection, manual
normalization and an intelligence workbench with filters, summary metrics,
source-aware item rows and a normalized-content detail panel.

## Intelligence UI

Phase 4 adds an analyst-facing workbench over normalized items. The UI supports:

- Search over title, URL, summary, raw content and normalized content
- Filtering by source, status, language and duplicate state
- Summary metrics for total, raw, normalized, duplicate and error states
- Language and top-source distribution summaries
- Item detail review without rendering untrusted HTML

The API remains server-filtered so the browser does not need to download the
full item corpus.

## AI Enrichment

Phase 5 adds one AI enrichment row per item. Enrichment is intentionally
separate from normalized items so model output can be audited and refreshed
without changing the original collected intelligence.

The OpenRouter client calls the OpenAI-compatible chat completions endpoint and
requests structured JSON. The default model is `openrouter/free`, configurable
through `OPENROUTER_MODEL`. The API key must be provided through
`OPENROUTER_API_KEY` and must never be committed.

Enrichment output includes:

- Summary
- Severity
- Confidence
- Tags
- CVEs
- IOCs
- MITRE ATT&CK techniques
- Recommended defensive actions

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

The foundation configures structured JSON logging with `structlog`. Request
IDs, correlation IDs, metrics and OpenTelemetry are planned for future phases.

## Security Boundary

Phase 5 sends normalized item text to the configured AI provider only when a
manual enrichment endpoint is called. Source URLs, feed bodies and AI responses
are untrusted input. The UI renders enrichment fields as text and never executes
or injects external HTML. The `users` table exists so authentication and RBAC
can be added later without reshaping the foundation.

## Future direction

The architecture is intentionally simple and AWS-ready without adding AWS dependencies prematurely.
