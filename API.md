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

Phase 1 exposes system status and source management endpoints only.

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
