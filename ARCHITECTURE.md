# CyberSec Architecture

## Current phase

Phase 10 - Reports.

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
- `cybersec_api.api.ask`: Ask CyberSec cited question answering route
- `cybersec_api.api.stories`: story clustering and story analytics routes
- `cybersec_api.api.collection`: manual collection routes
- `cybersec_api.api.enrichment`: manual AI enrichment routes
- `cybersec_api.api.intelligence`: cyber entity synchronization and analytics routes
- `cybersec_api.api.normalization`: manual normalization routes
- `cybersec_api.api.items`: collected item routes
- `cybersec_api.api.reports`: report generation, listing and Markdown export
- `cybersec_api.collectors`: RSS collection and scheduler logic
- `cybersec_api.ask`: local retrieval and OpenRouter-backed answer generation
- `cybersec_api.enrichment`: OpenRouter client and enrichment orchestration
- `cybersec_api.intelligence`: derived entity extraction and risk scoring
- `cybersec_api.normalizers`: text extraction, language detection and duplicate marking
- `cybersec_api.reports`: deterministic report assembly over stories and items
- `cybersec_api.stories`: local embedding generation and clustering
- `cybersec_api.war_room`: operational snapshot aggregation
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

Current derived intelligence tables:

- `enrichments`
- `cyber_entities`
- `stories`
- `story_items`
- `reports`
- `report_stories`
- `report_items`

Future phases may add reports, departments, watchlists, audit logs, alerts and
model usage.

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
CSS. The current shell is organized as a contextual cyber intelligence product
instead of one long scrolling page. Analysts move between dedicated workspaces:

- War Room for operational triage
- Ask for cited RAG questions over current intelligence
- Reports for persistent analyst briefings and Markdown export
- Stories for threat narratives and exact source articles
- Entities for CVEs, IOCs, MITRE techniques, tags and threat actors
- News Feed for collected source material and item-level evidence
- Sources for feed health and collection control

## Intelligence UI

The analyst-facing UI supports:

- Search over title, URL, summary, raw content and normalized content
- Filtering by source, status, language and duplicate state
- Summary metrics for total, raw, normalized, duplicate and error states
- Language and top-source distribution summaries
- Item detail review without rendering untrusted HTML
- Contextual links from stories to exact news items
- Contextual links from news items to extracted cyber entities
- Contextual links from entities back to stories and source articles
- Trusted external references for CVEs and MITRE ATT&CK techniques

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

## Cyber Intelligence

Phase 6 derives structured cyber entities from completed enrichments. The
derived `cyber_entities` table stores one entity occurrence per item and keeps
the original enrichment separate for auditability.

Supported entity classes:

- CVEs
- IOCs
- MITRE ATT&CK techniques
- Tags
- Threat actors using generic APT, TA, UNC and FIN patterns

Each entity receives a deterministic risk score based on enrichment severity,
confidence and entity type. Synchronization is manual through
`POST /intelligence/sync`, so operators control when model-derived intelligence
is promoted into the analytical layer.

The workbench exposes entity counts, high-risk entities, aggregate entity radar
and per-item entity evidence.

## Stories

Phase 7 clusters enriched intelligence into analyst-facing stories. It uses
deterministic local embeddings generated from normalized item text, AI summaries
and extracted cyber entities, then stores cluster centroids in PostgreSQL using
the `vector(384)` type from pgvector.

The story sync process:

- Loads normalized, non-duplicate items with completed enrichment
- Builds local 384-dimensional embeddings without external API calls
- Groups items by embedding similarity and shared cyber entities
- Rebuilds `stories` and `story_items` as a derived analytical layer
- Preserves links back to original collected items

Stories are intentionally rebuildable. They are not yet analyst-approved cases,
incidents or reports.

## War Room

Phase 8 adds a Cyber War Room view over the existing analytical layers. It does
not add new tables. The War Room endpoint aggregates current stories, cyber
entities, enriched items, fresh collection activity and source health into one
operator-facing snapshot.

The War Room snapshot includes:

- Operating mode derived from story risk and high-risk entity volume
- Risk queue ordered by active story risk
- Entity pulse grouped by entity type and normalized value
- Operational timeline combining recent stories and items
- Source health states based on enabled status, fetch freshness and errors

This phase remains read-only over derived intelligence and does not create
alerts, reports, cases or RAG answers.

## Ask CyberSec

Phase 9 adds cited question answering over the existing intelligence graph. It
does not add new tables and does not persist conversations yet.

Ask CyberSec retrieves evidence from normalized, enriched, non-duplicate news
items and joins the current source, cyber entity and story relationships. The
retrieval score combines deterministic local text embeddings, query token
overlap and entity matches.

Answer generation has two modes:

- `openrouter`: uses the configured OpenRouter chat model to synthesize an
  evidence-bound answer.
- `local` or `local_fallback`: returns an extractive answer from the retrieved
  citations when AI is disabled or unavailable.

Every response returns citations that link back to exact news items, related
stories, entities and original source URLs. Ask CyberSec is intended for
analyst triage and does not replace source review.

## Reports

Phase 10 adds persistent draft reports generated from current story clusters.
Reports are deterministic and do not call an AI provider. A report stores a
Markdown body plus relationships back to the exact stories and source news items
used as evidence.

Report generation can include exact story ids or a filtered set of top stories
by severity and risk. The generated artifact includes:

- Executive summary
- Risk story sections
- Key entities
- Evidence citations
- Analyst notes

Reports are drafts, not approved publications. Future phases may add analyst
approval, scheduled reports, PDF export, recipients and audit trails.

## Contextual Navigation

The contextual navigation layer is read-only and built over existing derived
data. It introduces API contracts that make relationships explicit:

- `GET /items/{item_id}/context` returns one news item, its extracted entities
  and its linked stories.
- `GET /intelligence/entities/context` returns one entity aggregate, related
  news items, related stories and trusted external reference URLs.

The frontend uses these contracts so an analyst can inspect how one source
article becomes normalized intelligence, how AI enrichment created CVEs or
techniques, and how those objects connect into a story.

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

Phase 10 treats War Room, Ask and Reports data as untrusted analytical metadata
aggregated from feeds, AI responses, extracted entities and story summaries. The
UI renders those values as text and never executes or injects external HTML. The
`users` table exists so authentication and RBAC can be added later without
reshaping the foundation.

## Future direction

The architecture is intentionally simple and AWS-ready without adding AWS dependencies prematurely.
