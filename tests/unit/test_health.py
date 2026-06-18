import pytest
from app.core.config import settings
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_liveness(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_k8s_liveness_alias(client: AsyncClient) -> None:
    response = await client.get("/health/live")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_readiness(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == settings.app_name
    assert body["database"] == "ok"


@pytest.mark.asyncio
async def test_request_id_header(client: AsyncClient) -> None:
    response = await client.get("/health/live", headers={"X-Request-ID": "test-req-1"})
    assert response.headers.get("X-Request-ID") == "test-req-1"
