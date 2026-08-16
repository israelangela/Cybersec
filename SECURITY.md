# CyberSec Security

## Current posture

Phase 5 creates AI enrichment on top of normalized RSS collection. It does not
implement authentication, RBAC or RAG yet.

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

Future phases will add Argon2id password handling, secure cookies, HttpOnly, SameSite, CSRF protection, rate limiting, RBAC, audit logs, SSRF controls, malicious feed handling, prompt-injection defenses and authorized retrieval for RAG.

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
