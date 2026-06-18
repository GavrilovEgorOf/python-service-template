from sqlalchemy import asc, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import cache_delete, cache_get, cache_set
from app.db.models import Item
from app.domain.exceptions import ItemAlreadyExistsError, ItemNotFoundError
from app.schemas.item import ItemCreate, ItemListParams, ItemRead, PaginatedResponse

_SORT_COLUMNS = {
    "id": Item.id,
    "name": Item.name,
    "created_at": Item.created_at,
}


def _cache_key(item_id: int) -> str:
    return f"item:{item_id}"


async def create_item(session: AsyncSession, payload: ItemCreate) -> ItemRead:
    item = Item(name=payload.name, description=payload.description)
    session.add(item)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ItemAlreadyExistsError("Item with this name already exists") from exc
    await session.refresh(item)
    return ItemRead.model_validate(item)


async def list_items(
    session: AsyncSession,
    params: ItemListParams,
) -> PaginatedResponse[ItemRead]:
    sort_key = params.sort.lstrip("-")
    column = _SORT_COLUMNS.get(sort_key, Item.id)
    ordering = desc(column) if params.sort.startswith("-") else asc(column)

    total = await session.scalar(select(func.count()).select_from(Item))
    result = await session.scalars(
        select(Item).order_by(ordering).limit(params.limit).offset(params.offset)
    )
    items = [ItemRead.model_validate(item) for item in result.all()]
    return PaginatedResponse[ItemRead](
        items=items,
        total=int(total or 0),
        limit=params.limit,
        offset=params.offset,
    )


async def get_item(session: AsyncSession, item_id: int) -> ItemRead:
    cached = await cache_get(_cache_key(item_id))
    if cached is not None:
        return ItemRead.model_validate_json(cached)

    item = await session.get(Item, item_id)
    if item is None:
        raise ItemNotFoundError("Item not found")

    read = ItemRead.model_validate(item)
    await cache_set(
        _cache_key(item_id),
        read.model_dump_json(),
        ttl_seconds=settings.cache_ttl_seconds,
    )
    return read


async def invalidate_item_cache(item_id: int) -> None:
    await cache_delete(_cache_key(item_id))
