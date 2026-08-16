# Database Schema

## Engine

CyberSec uses PostgreSQL as the source of truth. Schema evolution is managed by
Alembic.

Current development image:

```text
pgvector/pgvector:pg18
```

The current verified runtime is PostgreSQL 18.6 with the `vector` extension
available for local story embeddings.

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
- `normalized_title`
- `normalized_content`
- `normalized_hash`
- `language`
- `is_duplicate`
- `duplicate_of_item_id`
- `normalization_error`
- `normalized_at`
- `published_at`
- `collected_at`
- `created_at`
- `updated_at`

## Constraints

- `users.email` is unique.
- `sources.url` is unique.
- `items.url` is unique.
- `items.content_hash` is unique.
- `items.normalized_hash` is indexed.
- `items.language` is indexed.
- `items.source_id` references `sources.id` with cascade delete.
- `items.duplicate_of_item_id` references `items.id` with set null on delete.
- `items.source_id` and `items.external_id` are unique as a pair.

## Future Tables

Future phases may add:

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

## Phase 2 Notes

Phase 2 uses the existing `sources` and `items` tables. No new migration is
required.

RSS collection creates `items` with status `raw`. Deduplication checks:

- `items.url`
- `items.content_hash`
- `items.source_id` plus `items.external_id`

## Phase 3 Notes

Phase 3 adds migration `0002_item_normalization`.

Normalization preserves the original raw collection fields and adds normalized
metadata on the same `items` row. Duplicates are marked with `status =
duplicate`, `is_duplicate = true` and `duplicate_of_item_id` pointing to the
first normalized item with the same normalized hash.

## Phase 4 Notes

Phase 4 does not require a database migration.

The intelligence UI uses the existing `items` and `sources` tables. Backend
queries filter by existing columns such as `source_id`, `status`, `language`,
`is_duplicate`, `title`, `url`, `summary`, `raw_content`, `normalized_title` and
`normalized_content`.

## Phase 5 Notes

Phase 5 adds migration `0003_enrichments`.

### `enrichments`

Stores one AI enrichment result per item.

Columns:

- `id`
- `item_id`
- `provider`
- `model`
- `status`
- `summary`
- `severity`
- `confidence`
- `tags`
- `cves`
- `iocs`
- `mitre_attack`
- `recommended_actions`
- `raw_response`
- `error`
- `enriched_at`
- `created_at`
- `updated_at`

Constraints:

- `enrichments.item_id` is unique.
- `enrichments.item_id` references `items.id` with cascade delete.
- `enrichments.status` is indexed.
- `enrichments.severity` is indexed.

## Phase 6 Notes

Phase 6 adds migration `0004_cyber_entities`.

### `cyber_entities`

Stores derived cyber intelligence entities extracted from completed enrichment
rows. One row represents one entity occurrence in one item.

Columns:

- `id`
- `item_id`
- `enrichment_id`
- `entity_type`
- `value`
- `normalized_value`
- `severity`
- `confidence`
- `risk_score`
- `evidence`
- `first_seen_at`
- `last_seen_at`
- `created_at`
- `updated_at`

Constraints:

- `cyber_entities.item_id` references `items.id` with cascade delete.
- `cyber_entities.enrichment_id` references `enrichments.id` with cascade delete.
- `item_id`, `entity_type` and `normalized_value` are unique as a group.
- `entity_type`, `normalized_value`, `severity` and `risk_score` are indexed.

Entity types currently derived:

- `cve`
- `ioc`
- `mitre_attack`
- `tag`
- `threat_actor`

## Phase 7 Notes

Phase 7 adds migration `0005_stories`.

The database image now uses `pgvector/pgvector:pg18` so the `vector` extension
is available in development. The migration creates the extension if needed.

### `stories`

Stores deterministic story clusters derived from normalized, enriched items and
synchronized cyber entities.

Columns:

- `id`
- `title`
- `summary`
- `status`
- `severity`
- `risk_score`
- `item_count`
- `entity_count`
- `keywords`
- `entity_fingerprint`
- `embedding`
- `first_seen_at`
- `last_seen_at`
- `created_at`
- `updated_at`

Constraints:

- `embedding` uses `vector(384)`.
- `entity_fingerprint`, `risk_score` and `severity` are indexed.

### `story_items`

Stores the many-to-many relationship between stories and items.

Columns:

- `story_id`
- `item_id`
- `relevance_score`
- `created_at`

Constraints:

- `story_id` references `stories.id` with cascade delete.
- `item_id` references `items.id` with cascade delete.
- `story_id` and `item_id` are the composite primary key.
- `item_id` is indexed.

## Phase 8 Notes

Phase 8 does not require a database migration.

The Cyber War Room is a read-only aggregate over existing `stories`,
`story_items`, `cyber_entities`, `enrichments`, `items` and `sources` rows.
Source health, operating mode, risk queue, entity pulse and timeline values are
computed at request time.
