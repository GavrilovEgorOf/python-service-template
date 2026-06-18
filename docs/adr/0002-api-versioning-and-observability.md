# ADR 0002: API versioning and observability defaults

## Status

Accepted

## Context

Services in production need stable external contracts, probe-friendly health endpoints, and consistent tracing without every team re-deciding conventions.

## Decision

1. **Versioned API** lives under `/api/v1`.
2. **Kubernetes probes** use aliases at `/health/live` and `/health/ready` (same handlers as versioned routes).
3. **Readiness** validates PostgreSQL and Redis (Redis may be `disabled` when not configured).
4. **Request correlation** via `X-Request-ID` middleware bound into structlog context.
5. **Metrics** exposed at `/metrics` (Prometheus) when `METRICS_ENABLED=true`.
6. **Traces** exported via OTLP when `OTEL_ENABLED=true`.
7. **Idempotency** for mutating endpoints uses Redis-backed `Idempotency-Key` storage with TTL.

## Consequences

- Clients must migrate to `/api/v1` for business endpoints.
- Load balancers can keep simple `/health/*` paths.
- Local dev works without Redis/OTel, but production should enable both.
