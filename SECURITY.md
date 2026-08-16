# CyberSec Security

## Current posture

Phase 12 creates an enterprise governance layer for departments, internal user
identities, role memberships, audit events and model usage visibility. It does
not implement login, enforced RBAC, external delivery or automated response yet.

## Security rules

- Never commit real secrets.
- Do not log passwords, tokens, API keys or authorization headers.
- Treat all feed content as untrusted input.
- Treat AI provider responses as untrusted input.
- Never commit `OPENROUTER_API_KEY` or any other provider secret.
- Use Alembic for all schema changes.
- Keep database access behind SQLAlchemy sessions.
- Prefer typed configuration through environment variables.
- Keep `.env` untracked and use `.env.example` for safe defaults.
- Run dependency checks before publishing changes.

## Planned controls

Future phases will add Argon2id password handling, secure cookies, HttpOnly,
SameSite, CSRF protection, rate limiting, enforced RBAC, stronger SSRF controls,
malicious feed handling, prompt-injection defenses, authorized retrieval for RAG
and production observability.

## Phase 0 Threat Notes

The main Phase 0 risks are configuration mistakes, accidental secret commits and
dependency drift. The current repository mitigates those risks with `.gitignore`,
safe example configuration, Dockerized runtime checks and `npm audit`.

## Phase 1 Threat Notes

Source URLs are stored but not fetched in this phase. Future collection must
treat every source URL and response body as untrusted input and add SSRF,
redirect, timeout and content-size controls before any network retrieval.

## Phase 2 Threat Notes

RSS collection fetches enabled RSS source URLs. Current controls include
`http/https` URL validation, request timeout, redirect limit and maximum response
size. Phase 3 should add stronger normalization and sanitization before
presenting external content beyond plain text summaries.

## Phase 3 Threat Notes

Normalization extracts plain text from untrusted HTML and ignores script, style
and noscript blocks. The UI renders normalized content as React text, not raw
HTML. This is not a replacement for future content-security, SSRF, malware
scanning or prompt-injection controls.

## Phase 4 Threat Notes

The intelligence workbench displays normalized content and source metadata as
text. It never injects external feed HTML into the DOM. External original URLs
open in a new tab with `noreferrer`. Authentication, RBAC and per-user access
control remain future work.

## Phase 5 Threat Notes

AI enrichment sends normalized item title/content, source name and URL to the
configured OpenRouter-compatible provider only when manually triggered. The API
key is read from environment variables and is never stored in the repository.
Model output is validated as structured JSON where supported, persisted as
untrusted data and rendered as text. Prompt-injection defenses, tenant isolation,
usage budgets and full audit logging remain future work.

## Phase 6 Threat Notes

Cyber intelligence entities are derived from untrusted model output and must be
treated as analyst-assistive metadata, not verified truth. The sync job does not
call external providers, but it promotes model-derived CVEs, IOCs, MITRE tags
and actor identifiers into indexed tables. The UI renders all entities as text.
Future phases should add provenance review, confidence thresholds, suppression
lists, audit trails and analyst approval workflows before automation or alerting.

## Phase 7 Threat Notes

Story clusters are derived from untrusted feed content and untrusted model
output. The sync job does not call external providers; embeddings are generated
locally with deterministic hashing and stored in PostgreSQL through pgvector.
Stories should be treated as analyst-assistive grouping metadata, not verified
incident conclusions. Future phases should add reviewer workflows, provenance
drill-down, cluster suppression and audit logs before using stories to trigger
automated response.

## Phase 8 Threat Notes

The War Room aggregates untrusted feed content, untrusted AI output and derived
story metadata into a higher-visibility operational surface. It is read-only and
does not trigger alerts or response actions. Operators should treat the risk
queue, operating mode and source health as triage aids until authentication,
RBAC, audit logging, analyst approval and incident workflow controls exist.

## Phase 9 Threat Notes

Ask CyberSec retrieves and summarizes untrusted feed content, untrusted AI
output and derived entities. Citations provide traceability, not proof. Operators
must review the linked source items before taking defensive action. Ask does not
persist conversations yet, does not enforce per-user authorization and does not
protect against prompt injection beyond evidence-only prompting and plain-text
rendering. Future phases should add authorized retrieval, prompt-injection
testing, audit logs, usage limits and model-cost controls.

## Phase 10 Threat Notes

Reports persist summaries and Markdown generated from untrusted source feeds,
untrusted AI enrichment and derived analytical metadata. Reports should be
treated as drafts until reviewed by an analyst. Markdown is rendered as text in
the current UI; future rich rendering must sanitize content. Reports do not
implement approval workflows, recipients, file signing, redaction, access
control or audit trails yet.

## Phase 11 Threat Notes

Alerts are derived from untrusted feed content, untrusted AI enrichment and
derived cyber entities. They are triage prompts, not proof of compromise.
Operators must review the linked source news, story and entity evidence before
taking action. Phase 11 does not send emails, webhooks or automated response
actions. Future phases must add authentication, RBAC, audit logs, suppression
rules, notification controls and approval workflows before external delivery or
response automation is enabled.

## Phase 12 Threat Notes

Enterprise users are internal governance identities, not authenticated login
accounts. Department memberships and permissions are stored for future RBAC, but
Phase 12 does not enforce endpoint authorization. Audit events and model usage
records improve traceability but are not tamper-proof without authentication,
append-only controls and administrator separation. Future production work must
add authenticated actors, authorization middleware, immutable audit storage,
rate limits, secrets scanning in CI and operational monitoring before this is
used as a controlled enterprise system.
