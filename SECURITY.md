# CyberSec Security

## Current posture

Phase 2 creates RSS collection on top of source management. It does not
implement authentication, RBAC, AI enrichment or RAG yet.

## Security rules

- Never commit real secrets.
- Do not log passwords, tokens, API keys or authorization headers.
- Treat all future feed content as untrusted input.
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
