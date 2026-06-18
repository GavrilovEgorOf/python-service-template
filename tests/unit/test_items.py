import asyncio

import pytest
from app.core.security import create_access_token
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_item(client: AsyncClient) -> None:
    create_response = await client.post(
        "/api/v1/items",
        json={"name": "alpha", "description": "first item"},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "alpha"

    list_response = await client.get("/api/v1/items")
    assert list_response.status_code == 200
    body = list_response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1

    get_response = await client.get(f"/api/v1/items/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["description"] == "first item"


@pytest.mark.asyncio
async def test_create_duplicate_item_returns_conflict(client: AsyncClient) -> None:
    payload = {"name": "duplicate", "description": None}
    first = await client.post("/api/v1/items", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/v1/items", json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_get_missing_item_returns_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/items/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_pagination(client: AsyncClient) -> None:
    for idx in range(3):
        await client.post("/api/v1/items", json={"name": f"item-{idx}"})

    response = await client.get("/api/v1/items", params={"limit": 2, "offset": 1, "sort": "-id"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["limit"] == 2
    assert body["offset"] == 1
    assert len(body["items"]) == 2


@pytest.mark.asyncio
async def test_idempotency_replays_response(client: AsyncClient) -> None:
    headers = {"Idempotency-Key": "key-123"}
    payload = {"name": "once", "description": "idem"}
    first = await client.post("/api/v1/items", json=payload, headers=headers)
    second = await client.post("/api/v1/items", json=payload, headers=headers)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json() == second.json()


@pytest.mark.asyncio
async def test_idempotency_conflict_on_different_payload(client: AsyncClient) -> None:
    headers = {"Idempotency-Key": "key-456"}
    await client.post("/api/v1/items", json={"name": "a"}, headers=headers)
    conflict = await client.post("/api/v1/items", json={"name": "b"}, headers=headers)
    assert conflict.status_code == 422


@pytest.mark.asyncio
async def test_idempotency_race_only_one_item_created(client: AsyncClient) -> None:
    headers = {"Idempotency-Key": "race-key-789"}
    payload = {"name": "race-item", "description": "parallel"}

    responses = await asyncio.gather(
        client.post("/api/v1/items", json=payload, headers=headers),
        client.post("/api/v1/items", json=payload, headers=headers),
    )

    statuses = sorted(response.status_code for response in responses)
    assert 201 in statuses
    assert any(code in {201, 409} for code in statuses)

    list_response = await client.get("/api/v1/items")
    names = [item["name"] for item in list_response.json()["items"]]
    assert names.count("race-item") == 1


@pytest.mark.asyncio
async def test_auth_required_when_enabled(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.core.config.settings.auth_disabled", False)
    response = await client.get("/api/v1/items")
    assert response.status_code == 401

    authed = await client.get("/api/v1/items", headers={"X-API-Key": "test-api-key"})
    assert authed.status_code == 200


@pytest.mark.asyncio
async def test_bearer_jwt_auth(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.config.settings.auth_disabled", False)
    token = create_access_token("user-42", roles=("user",))
    response = await client.get("/api/v1/items", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_invalid_jwt_rejected(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.core.config.settings.auth_disabled", False)
    response = await client.get(
        "/api/v1/items", headers={"Authorization": "Bearer not-a-valid-jwt"}
    )
    assert response.status_code == 401
