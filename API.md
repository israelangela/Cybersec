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

Phase 2 exposes system status, source management, RSS collection and item
listing endpoints.

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
- `limit`: number of items, from `1` to `200`

### `GET /items/{item_id}`

Returns one collected item by UUID.

Missing items return `404 Not Found`.

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
