# CyberSec Security

## Phase 0 posture

Phase 0 creates the application foundation and database schema. It does not implement authentication, RBAC or external content ingestion yet.

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
