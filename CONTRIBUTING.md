# Contributing

Thanks for improving this FastAPI golden-path template. This guide covers fork workflow, local development, testing, and what we expect in pull requests.

**Audience:** remote EU/US senior backend engineers shipping production microservices.

## Fork and clone

1. Fork [python-service-template](https://github.com/GavrilovEgorOf/python-service-template) on GitHub.
2. Clone your fork and add upstream:

```bash
git clone git@github.com:<you>/python-service-template.git
cd python-service-template
git remote add upstream git@github.com:GavrilovEgorOf/python-service-template.git
```

3. Create a feature branch from `main`:

```bash
git fetch upstream
git checkout -b feat/short-description upstream/main
```

4. Keep your fork current before opening a PR:

```bash
git fetch upstream
git rebase upstream/main
```

For a new service derived from the template (not upstream contributions), fork once, rename immediately, and treat your fork as the service repo. See [docs/CUSTOMIZE.md](docs/CUSTOMIZE.md).

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

cp .env.example .env
docker compose up -d postgres redis
alembic upgrade head
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Swagger UI: http://localhost:8000/docs

## Rename the service

Before domain work, rename the template so app name, package name, and OTEL identifiers stay consistent:

```bash
python scripts/rename_service.py billing-api
```

The script replaces `python-service-template` / `python_service_template` across tracked files (skips `.git` and `.venv`). Re-run with `--old-name` if you rename again.

Verify:

- `pyproject.toml` → `[project].name`
- `app/core/config.py` → default `app_name` and `otel_service_name`
- `.env` → `APP_NAME`, `OTEL_SERVICE_NAME`

## Code layout

Follow the layered structure documented in [docs/adr/0001-project-structure.md](docs/adr/0001-project-structure.md):

| Layer | Path | Responsibility |
|-------|------|----------------|
| HTTP | `app/api/` | Routes, status codes, dependency injection |
| Business | `app/services/` | Domain logic, no FastAPI imports |
| Persistence | `app/db/` | SQLAlchemy models and session |
| DTOs | `app/schemas/` | Pydantic request/response models |
| Cross-cutting | `app/core/` | Config, logging, telemetry |

Keep route handlers thin; put logic in services and test there when possible.

## Running tests

All tests live under `tests/`. CI runs the full suite with coverage (`fail_under = 75` in `pyproject.toml`).

### Full suite (what CI runs)

Requires Docker for Testcontainers PostgreSQL. Without Docker, tests fall back to in-memory SQLite (see `tests/conftest.py`).

```bash
pytest --cov=app --cov-report=term-missing
```

### Unit tests

Unit tests exercise **business logic in isolation** — typically `app/services/*` with a mocked `AsyncSession` or in-memory fakes. They should not start FastAPI, hit HTTP, or require Docker.

Conventions when adding unit tests:

- Place them in `tests/unit/` (create the directory) or name files `test_*_unit.py`.
- Mark with `@pytest.mark.unit` and register the marker in `pyproject.toml` if you split CI jobs later.
- No `client` fixture; no Testcontainers.

Example run (once you add markers):

```bash
pytest -m unit
```

### Integration tests

Integration tests exercise **HTTP + database** together via the `client` fixture in `conftest.py`. They use:

- `httpx.AsyncClient` against the ASGI app
- Real async SQLAlchemy sessions
- PostgreSQL 16 via Testcontainers when Docker is available, otherwise SQLite fallback

Existing tests (`test_health.py`, `test_items.py`) are integration-style API tests.

```bash
pytest tests/test_items.py tests/test_health.py -v
```

Ensure Docker Desktop (or the Docker daemon) is running before relying on Postgres-backed behavior.

### Static checks

Match CI locally before pushing:

```bash
ruff check app tests
mypy app
```

## Pre-commit (recommended)

The repo does not ship a `.pre-commit-config.yaml` by default. Teams should add one so local commits mirror CI.

1. Install hooks:

```bash
pip install pre-commit
```

2. Add `.pre-commit-config.yaml` at the repo root:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.6
    hooks:
      - id: ruff
        args: [--fix]
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic-settings, sqlalchemy, fastapi]
        args: [app]
```

3. Install and run:

```bash
pre-commit install
pre-commit run --all-files
```

Adjust `rev` pins to match your `pyproject.toml` dev dependencies. Add a `pytest` hook only if your team accepts the slower commit cycle (Testcontainers needs Docker).

## Pull request checklist

Before opening a PR against `main`:

- [ ] Branch is rebased on latest `upstream/main` (for template contributions) or your team's default branch (for forked services).
- [ ] Service renamed if this is a new derived project (`scripts/rename_service.py`).
- [ ] `ruff check app tests` passes.
- [ ] `mypy app` passes (strict mode).
- [ ] `pytest --cov=app --cov-report=term-missing` passes with coverage ≥ 75%.
- [ ] New behavior has tests (unit for service logic, integration for routes/DB).
- [ ] Alembic migration included for schema changes (`alembic revision --autogenerate -m "..."`; review generated SQL).
- [ ] `.env.example` updated for new settings (no secrets committed).
- [ ] README or ADR updated if structure, defaults, or operational behavior changed.
- [ ] PR description explains **why**, not only what; link related issues if any.

### PR title and scope

- One logical change per PR (feature, fix, or docs — not all three).
- Use imperative titles: `Add idempotency middleware`, `Fix readiness probe when DB pool exhausted`.
- Breaking changes: call out in the PR body and note migration/rollback steps.

### What CI runs

GitHub Actions (`.github/workflows/ci.yml`) on every push/PR to `main`:

1. `ruff check app tests`
2. `mypy app`
3. `pytest --cov=app --cov-report=term-missing` (Docker available on `ubuntu-latest` runners)

Fix CI failures locally; do not disable checks to merge.

## Questions

- Architecture: [docs/adr/0001-project-structure.md](docs/adr/0001-project-structure.md)
- Post-clone customization: [docs/CUSTOMIZE.md](docs/CUSTOMIZE.md)
