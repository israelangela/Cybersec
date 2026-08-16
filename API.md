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

Phase 0 exposes system status endpoints only. Source management endpoints belong
to Phase 1 and are intentionally not implemented yet.
