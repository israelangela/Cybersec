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

Phase 6 exposes system status, source management, RSS collection, item listing,
item statistics, item normalization, AI enrichment and cyber intelligence
entity endpoints.

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

### `GET /intelligence/items/{item_id}/entities`

Returns all cyber entity occurrences derived for one item.

### `GET /intelligence/stats`

Returns total entities, unique entities, high-risk entity count, distribution by
entity type and top-risk entities for the workbench.

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
