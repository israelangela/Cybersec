# Database Schema

## Engine

CyberSec uses PostgreSQL as the source of truth. Schema evolution is managed by
Alembic.

Current development image:

```text
postgres:latest
```

The current verified runtime is PostgreSQL 18.6.

## Phase 0 Tables

### `users`

Stores application users for future authentication and RBAC.

Columns:

- `id`
- `email`
- `full_name`
- `hashed_password`
- `is_active`
- `is_superuser`
- `created_at`
- `updated_at`

### `sources`

Stores intelligence sources for future source management and collection.

Columns:

- `id`
- `name`
- `url`
- `source_type`
- `description`
- `weight`
- `is_enabled`
- `last_fetched_at`
- `last_error`
- `error_count`
- `created_at`
- `updated_at`

### `items`

Stores raw intelligence items collected from sources in future phases.

Columns:

- `id`
- `source_id`
- `title`
- `url`
- `external_id`
- `content_hash`
- `summary`
- `raw_content`
- `status`
- `published_at`
- `collected_at`
- `created_at`
- `updated_at`

## Constraints

- `users.email` is unique.
- `sources.url` is unique.
- `items.url` is unique.
- `items.content_hash` is unique.
- `items.source_id` references `sources.id` with cascade delete.
- `items.source_id` and `items.external_id` are unique as a pair.

## Future Tables

Future phases may add:

- `enrichments`
- `stories`
- `reports`
- `departments`
- `watchlists`
- `topics`
- `ask_conversations`
- `ask_messages`
- `audit_logs`
- `scheduled_reports`
- `alerts`
- `model_usage`

## Phase 1 Notes

Phase 1 uses the existing `sources` table. No new migration is required.

The application now manages source metadata but does not collect source content.
Fields such as `last_fetched_at`, `last_error` and `error_count` are reserved
for Phase 2 collection jobs.
