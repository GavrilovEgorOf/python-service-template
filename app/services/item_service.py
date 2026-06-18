from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Item
from app.schemas.item import ItemCreate


class ItemAlreadyExistsError(Exception):
    pass


class ItemNotFoundError(Exception):
    pass


async def create_item(session: AsyncSession, payload: ItemCreate) -> Item:
    item = Item(name=payload.name, description=payload.description)
    session.add(item)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ItemAlreadyExistsError from exc
    await session.refresh(item)
    return item


async def list_items(session: AsyncSession) -> list[Item]:
    result = await session.scalars(select(Item).order_by(Item.id))
    return list(result.all())


async def get_item(session: AsyncSession, item_id: int) -> Item:
    item = await session.get(Item, item_id)
    if item is None:
        raise ItemNotFoundError
    return item
