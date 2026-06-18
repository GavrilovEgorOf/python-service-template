# ADR 0001: Project structure

## Status

Accepted

## Context

We need a repeatable microservice layout that teams can clone, rename, and ship without re-deciding folder structure, tooling, or observability defaults.

## Decision

Use a layered FastAPI layout:

- `app/api` — HTTP routes and transport concerns
- `app/services` — business logic
- `app/db` — persistence models and session wiring
- `app/schemas` — Pydantic request/response models
- `app/core` — config, logging, telemetry

Health checks are split into liveness (`/health/live`) and readiness (`/health/ready`).

Database migrations live in Alembic. Integration tests use Testcontainers PostgreSQL.

## Consequences

- Easy to navigate for backend engineers joining a team
- Clear separation for unit vs integration testing
- Slightly more files than a single-module demo, but scales better for real services
