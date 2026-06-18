import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_integration_create_item(integration_client: AsyncClient) -> None:
    response = await integration_client.post(
        "/api/v1/items",
        json={"name": "integration-item", "description": "postgres"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "integration-item"
