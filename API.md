# API Reference

## Base URL

Local development:

```text
http://localhost:8000
```

## Endpoints

### `GET /health`

Liveness endpoint. It confirms the API process can respond.

Response:

```json
{
  "status": "ok",
  "service": "cybersec-api"
}
```

### `GET /ready`

Readiness endpoint. It confirms the API can reach PostgreSQL by executing
`SELECT 1`.

Response:

```json
{
  "status": "ready",
  "database": "ok"
}
```

## OpenAPI

FastAPI exposes generated API documentation locally:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Current Scope

Phase 10 exposes system status, source management, RSS collection, item listing,
item statistics, item normalization, AI enrichment, cyber intelligence entity
endpoints, story clustering endpoints, contextual navigation endpoints and the
Cyber War Room snapshot. It also exposes Ask CyberSec for cited RAG answers over
enriched intelligence and persistent report generation.

## Ask CyberSec

### `POST /ask`

Answers an analyst question using retrieved CyberSec evidence. Retrieval runs
over normalized, enriched, non-duplicate news items, their cyber entities and
linked stories.

Request:

```json
{
  "question": "Que sabemos de CVE-2026-19557?",
  "limit": 6,
  "use_ai": true
}
```

Fields:

- `question`: analyst question, from `3` to `1000` characters
- `limit`: maximum citations to return, from `1` to `12`
- `use_ai`: when true, OpenRouter is used if configured; otherwise CyberSec
  returns a local extractive answer with citations

Response sections:

- `answer`: cited answer text
- `mode`: `openrouter`, `local` or `local_fallback`
- `confidence`: heuristic confidence from retrieved evidence
- `citations`: exact source news items with source URL, story ids, entities and
  excerpts
- `follow_up_questions`: suggested next pivots

## Sources

### `GET /sources`

Lists sources ordered by name.

Optional query parameters:

- `is_enabled`: `true` or `false`
- `source_type`: `rss`, `web`, `api` or `other`

### `POST /sources`

Creates a source.

Request:

```json
{
  "name": "CISA Advisories",
  "url": "https://www.cisa.gov/news-events/cybersecurity-advisories",
  "source_type": "rss",
  "description": "Authoritative advisories source",
  "weight": "2.50",
  "is_enabled": true
}
```

Returns `201 Created`.

Duplicate URLs return `409 Conflict`.

### `GET /sources/{source_id}`

Returns one source by UUID.

Missing sources return `404 Not Found`.

### `PATCH /sources/{source_id}`

Updates a source. All fields are optional.

Request:

```json
{
  "is_enabled": false,
  "weight": "3.00"
}
```

Duplicate URLs return `409 Conflict`.

### `DELETE /sources/{source_id}`

Deletes a source and returns `204 No Content`.

Deleting a source cascades to related items through the database relationship.

## Items

### `GET /items`

Lists recently collected items.

Optional query parameters:

- `source_id`: filter by source UUID
- `status`: filter by item status
- `language`: filter by normalized language code
- `is_duplicate`: `true` or `false`
- `search`: search over title, URL, summary and normalized content
- `limit`: number of items, from `1` to `500`
- `offset`: result offset for pagination

Each item includes `source_name` when returned from list/detail endpoints.
Items may also include AI fields when enrichment exists:

- `ai_summary`
- `ai_severity`
- `ai_confidence`
- `ai_tags`
- `ai_cves`
- `ai_iocs`
- `ai_mitre_attack`
- `ai_recommended_actions`
- `enriched_at`

### `GET /items/stats`

Returns item counts for the intelligence UI.

Response:

```json
{
  "total": 4493,
  "raw": 0,
  "normalized": 4491,
  "duplicate": 2,
  "normalization_error": 0,
  "enriched": 10,
  "enrichment_error": 0,
  "languages": [],
  "sources": []
}
```

### `GET /items/{item_id}`

Returns one collected item by UUID.

Missing items return `404 Not Found`.

### `GET /items/{item_id}/context`

Returns one collected item together with its derived cyber entities and the
stories where the item appears.

The frontend uses this endpoint to move from an exact news item to its CVEs,
IOCs, MITRE techniques, tags, threat actors and related stories without losing
analyst context.

## Enrichment

### `GET /enrichment/items/{item_id}`

Returns the enrichment row for one item.

Missing enrichments return `404 Not Found`.

### `POST /enrichment/items/{item_id}/run`

Runs AI enrichment for one normalized, non-duplicate item.

Missing items return `404 Not Found`.

### `POST /enrichment/run`

Runs AI enrichment for pending normalized, non-duplicate items without an
existing enrichment.

Optional query parameters:

- `limit`: number of items to enrich, from `1` to `50`

## Cyber Intelligence

Cyber intelligence endpoints derive structured entities from completed AI
enrichments. They do not call the AI provider.

### `POST /intelligence/sync`

Synchronizes derived cyber entities from completed enrichments.

Optional query parameters:

- `limit`: number of enrichments to inspect, from `1` to `500`

Response:

```json
{
  "status": "ok",
  "enrichments_checked": 10,
  "entities_created": 45,
  "entities_deleted": 12,
  "skipped": 0
}
```

### `GET /intelligence/entities`

Lists aggregate cyber entities grouped by type and normalized value.

Optional query parameters:

- `entity_type`: `cve`, `ioc`, `mitre_attack`, `tag` or `threat_actor`
- `severity`: enrichment severity filter
- `min_score`: minimum risk score from `1` to `100`
- `search`: search entity value or type
- `limit`: number of entities, from `1` to `500`
- `offset`: result offset

### `GET /intelligence/entities/context`

Returns the contextual graph for one entity value.

Required query parameters:

- `entity_type`: `cve`, `ioc`, `mitre_attack`, `tag` or `threat_actor`
- `value`: raw or normalized entity value

Optional query parameters:

- `limit`: number of related news items, from `1` to `500`

Response sections:

- `entity`: aggregate entity risk, occurrences and seen dates
- `items`: exact news items that produced the entity
- `stories`: story clusters connected to those news items
- `external_references`: trusted external links such as NVD, CVE.org or MITRE
  ATT&CK when the entity type supports them

### `GET /intelligence/items/{item_id}/entities`

Returns all cyber entity occurrences derived for one item.

### `GET /intelligence/stats`

Returns total entities, unique entities, high-risk entity count, distribution by
entity type and top-risk entities for the workbench.

## Stories

Story endpoints derive clusters from normalized, enriched items and synchronized
cyber entities. They do not call the AI provider.

### `POST /stories/sync`

Rebuilds story clusters from enriched items.

Optional query parameters:

- `limit`: number of enriched items to inspect, from `1` to `500`
- `similarity_threshold`: clustering threshold from `0.1` to `0.95`

Response:

```json
{
  "status": "ok",
  "candidates": 25,
  "stories_created": 8,
  "story_items_created": 25,
  "stories_deleted": 8,
  "skipped": 0
}
```

### `GET /stories`

Lists story clusters ordered by risk and recency.

Optional query parameters:

- `severity`: story severity filter
- `min_score`: minimum story risk score from `1` to `100`
- `search`: search story title, summary or fingerprint
- `limit`: number of stories, from `1` to `500`
- `offset`: result offset

### `GET /stories/{story_id}`

Returns one story with linked items and relevance scores.

Missing stories return `404 Not Found`.

### `GET /stories/stats`

Returns total stories, high-risk stories, linked item count and top stories for
the workbench.

## War Room

### `GET /war-room`

Returns one operational snapshot for the Cyber War Room.

Optional query parameters:

- `limit`: number of queue, pulse, timeline and source rows, from `1` to `25`

Response sections:

- `summary`: operating mode and aggregate counts
- `risk_queue`: active stories ordered by risk
- `entity_pulse`: top entity groups ordered by risk and occurrence count
- `timeline`: recent story and item events
- `source_health`: source freshness and error status

## Reports

### `POST /reports/generate`

Creates a draft report from current story clusters and their cited source news.

Request:

```json
{
  "title": "Weekly CTI Executive Brief",
  "report_type": "executive",
  "severity": "high",
  "min_score": 70,
  "story_ids": [],
  "limit": 6
}
```

Fields:

- `title`: optional custom report title
- `report_type`: `executive`, `technical`, `daily` or any internal label
- `severity`: optional story severity filter
- `min_score`: optional story risk threshold from `1` to `100`
- `story_ids`: optional exact story ids to include
- `limit`: number of top stories to include when `story_ids` is empty

The response includes the persisted report, linked stories, linked source items
and generated Markdown body.

### `GET /reports`

Lists saved reports ordered by creation date.

Optional query parameters:

- `report_type`
- `status`
- `limit`: from `1` to `100`
- `offset`

### `GET /reports/{report_id}`

Returns a report with Markdown body, story links and cited source items.

### `GET /reports/{report_id}/markdown`

Returns the generated Markdown as `text/markdown`.

### `DELETE /reports/{report_id}`

Deletes a report and its report-story/report-item links.

## Collection

### `POST /collection/run`

Runs collection for all enabled RSS sources.

Response:

```json
{
  "status": "ok",
  "sources_checked": 1,
  "fetched": 10,
  "created": 8,
  "duplicates": 2,
  "skipped": 0,
  "errors": 0,
  "results": []
}
```

### `POST /collection/sources/{source_id}/run`

Runs collection for a single source.

Disabled sources and non-RSS sources return a `skipped` result rather than
fetching remote content.

## Normalization

### `POST /normalization/run`

Normalizes pending raw items. Optional query parameters:

- `limit`: number of pending items to normalize, from `1` to `500`

Response:

```json
{
  "status": "ok",
  "candidates": 2,
  "normalized": 1,
  "duplicates": 1,
  "failed": 0,
  "skipped": 0,
  "results": []
}
```

### `POST /normalization/items/{item_id}/run`

Normalizes one item by UUID.

Missing items return `404 Not Found`.
