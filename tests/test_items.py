import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_item(client: AsyncClient) -> None:
    create_response = await client.post(
        "/items",
        json={"name": "alpha", "description": "first item"},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "alpha"

    list_response = await client.get("/items")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = await client.get(f"/items/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["description"] == "first item"


@pytest.mark.asyncio
async def test_create_duplicate_item_returns_conflict(client: AsyncClient) -> None:
    payload = {"name": "duplicate", "description": None}
    first = await client.post("/items", json=payload)
    assert first.status_code == 201

    second = await client.post("/items", json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_get_missing_item_returns_not_found(client: AsyncClient) -> None:
    response = await client.get("/items/9999")
    assert response.status_code == 404
