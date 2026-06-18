# ADR 0003: Security and production hardening

## Status

Accepted

## Context

Template v0.4 exposed stub auth, open metrics, idempotency races, and permissive defaults unsuitable for production claims on a senior portfolio.

## Decision

1. **JWT validation** via PyJWT (iss, aud, exp, signature).
2. **Production settings validator** rejects `AUTH_DISABLED`, default secrets, and `DEBUG=true`.
3. **Idempotency** uses Redis `SET NX` with `in_progress` / `completed` lifecycle and lock TTL.
4. **Rate limiting** on item routes via Redis counters.
5. **Protected `/metrics`** endpoint (API key required).
6. **Audit middleware** logs user_id + request_id; optional DB persistence.
7. **Swagger disabled** when `DEBUG=false`.
8. **Helm chart** with `values-prod.yaml` production checklist.

## Consequences

- Local dev requires JWT secret or API key configuration.
- Redis becomes required for idempotency/rate-limit correctness under concurrency.
- Production misconfiguration fails fast at startup.
