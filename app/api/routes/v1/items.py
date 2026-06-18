from fastapi import APIRouter, Depends, Header, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.schemas.item import ItemCreate, ItemListParams, ItemRead, PaginatedResponse
from app.services import item_service
from app.services.idempotency_service import (
    begin_idempotent_request,
    complete_idempotent_request,
    fail_idempotent_request,
)

router = APIRouter(
    prefix="/items",
    tags=["items"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: ItemCreate,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> ItemRead:
    body = payload.model_dump()
    if idempotency_key:
        cached = await begin_idempotent_request(idempotency_key, body)
        if cached is not None:
            response.status_code = int(cached["status_code"])
            return ItemRead.model_validate(cached["response_body"])

    try:
        item = await item_service.create_item(session, payload)
    except Exception:
        if idempotency_key:
            await fail_idempotent_request(idempotency_key)
        raise

    if idempotency_key:
        await complete_idempotent_request(
            idempotency_key,
            body,
            status_code=status.HTTP_201_CREATED,
            response_body=item.model_dump(mode="json"),
        )
    return item


@router.get("", response_model=PaginatedResponse[ItemRead])
async def list_items(
    session: AsyncSession = Depends(get_db_session),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="id", pattern=r"^-?(id|name|created_at)$"),
) -> PaginatedResponse[ItemRead]:
    params = ItemListParams(limit=limit, offset=offset, sort=sort)
    return await item_service.list_items(session, params)


@router.get("/{item_id}", response_model=ItemRead)
async def get_item(
    item_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> ItemRead:
    return await item_service.get_item(session, item_id)
