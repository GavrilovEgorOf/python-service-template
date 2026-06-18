# Production checklist (values-prod.yaml)

Use this overlay when deploying to production clusters.

## Required secrets (`secrets.*`)

- `apiKey` — non-default API key for service clients
- `jwtSecretKey` — HS256 signing secret (rotate regularly)
- `metricsApiKey` — optional dedicated key for `/metrics` scraping
- `databaseUrl` — PostgreSQL async URL
- `redisUrl` — Redis URL for cache, idempotency, rate limits

## Required env (enforced by app startup validator)

- `ENVIRONMENT=production`
- `DEBUG=false`
- `AUTH_DISABLED=false`
- `JWT_SECRET_KEY` set and not a dev default
- `API_KEY` set and not a dev default

## Recommended production settings

- `AUDIT_LOG_PERSIST=true`
- `OTEL_ENABLED=true` and `OTEL_INSECURE=false`
- `RATE_LIMIT_ENABLED=true`
- Ingress + TLS termination
- NetworkPolicy: `/metrics` only from monitoring namespace
- HPA enabled (`values-prod.yaml`)

## Deploy example

```bash
helm upgrade --install api ./deploy/helm/python-service-template \
  -f deploy/helm/python-service-template/values.yaml \
  -f deploy/helm/python-service-template/values-prod.yaml \
  --set secrets.apiKey="$API_KEY" \
  --set secrets.jwtSecretKey="$JWT_SECRET"
```
