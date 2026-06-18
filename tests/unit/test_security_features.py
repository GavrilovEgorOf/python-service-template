import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.lifespan import lifespan
from app.main import create_app


@pytest.mark.asyncio
async def test_rate_limit_blocks_excessive_requests(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    monkeypatch.setattr(settings, "rate_limit_requests", 2)
    monkeypatch.setattr(settings, "rate_limit_window_seconds", 60)

    await client.get("/api/v1/items")
    await client.get("/api/v1/items")
    blocked = await client.get("/api/v1/items")
    assert blocked.status_code == 429


@pytest.mark.asyncio
async def test_metrics_endpoint_requires_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "metrics_enabled", True)
    monkeypatch.setattr(settings, "api_key", "metrics-test-key")
    monkeypatch.setattr(settings, "auth_disabled", True)

    app = create_app()
    transport = ASGITransport(app=app)
    async with lifespan(app), AsyncClient(transport=transport, base_url="http://test") as client:
        denied = await client.get("/metrics")
        assert denied.status_code == 403

        allowed = await client.get("/metrics", headers={"X-Metrics-Key": "metrics-test-key"})
        assert allowed.status_code == 200
        assert b"http_requests_total" in allowed.content
