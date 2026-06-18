# Python Service Template

[![CI](https://github.com/GavrilovEgorOf/python-service-template/actions/workflows/ci.yml/badge.svg)](https://github.com/GavrilovEgorOf/python-service-template/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Production-ready **FastAPI microservice template** for teams that want a golden path: async PostgreSQL, Alembic migrations, structured logging, OpenTelemetry hooks, Docker, and CI with ruff, mypy, pytest, and Testcontainers.

Built for **remote EU/US backend / platform engineering portfolios** and as a starting point for real services.

## Why this template

| Problem | What this repo gives you |
|---------|--------------------------|
| Every new service starts from scratch | Clone, rename, ship |
| Inconsistent project layout | Layered `api / services / db / schemas` structure |
| Missing prod basics | Health checks, migrations, observability hooks, CI |
| Tests without real Postgres | Testcontainers integration tests |

## Stack

- **FastAPI** + **Uvicorn**
- **SQLAlchemy 2 async** + **asyncpg** + **Alembic**
- **Pydantic Settings**, **structlog**
- **OpenTelemetry** (FastAPI + SQLAlchemy instrumentation)
- **pytest**, **Testcontainers**, **ruff**, **mypy**
- **Docker Compose** (API + Postgres + Redis)

## Quick start

```bash
git clone https://github.com/GavrilovEgorOf/python-service-template.git my-service
cd my-service
python scripts/rename_service.py my-service

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

cp .env.example .env
docker compose up -d postgres redis
alembic upgrade head
uvicorn app.main:app --reload
```

Open:

- Swagger UI: http://localhost:8000/docs
- Liveness: http://localhost:8000/health/live
- Readiness: http://localhost:8000/health/ready

## Rename for your service

```bash
python scripts/rename_service.py billing-api
```

Updates default app name, OTEL service name, and docs references.

## Project layout

```
app/
├── api/           # HTTP routes
├── core/          # config, logging, telemetry
├── db/            # SQLAlchemy models + session
├── schemas/       # Pydantic DTOs
├── services/      # business logic
└── main.py        # FastAPI app factory
alembic/           # database migrations
tests/             # pytest + Testcontainers
deploy/            # OTEL collector config
docs/adr/          # architecture decisions
scripts/           # rename helper
```

See [docs/adr/0001-project-structure.md](docs/adr/0001-project-structure.md).

## Example API

```bash
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name":"alpha","description":"first item"}'

curl http://localhost:8000/items
```

## Development commands

```bash
ruff check app tests
mypy app
pytest --cov=app --cov-report=term-missing
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Docker

```bash
cp .env.example .env
docker compose up --build
```

Optional OpenTelemetry collector:

```bash
docker compose --profile observability up --build
```

Set in `.env`:

```env
OTEL_ENABLED=true
OTEL_EXPORTER_ENDPOINT=http://otel-collector:4317
```

## CI

GitHub Actions runs on every push/PR:

1. `ruff check`
2. `mypy app`
3. `pytest` with coverage (Testcontainers requires Docker on the runner)

## What to customize first

1. Rename service via `scripts/rename_service.py`
2. Replace the sample `Item` domain with your own models/services
3. Add auth middleware (JWT/OAuth2) in `app/api/deps.py`
4. Wire Redis for caching or Celery for background jobs
5. Add Helm chart / Terraform module for your infra

## License

MIT — see [LICENSE](LICENSE).
