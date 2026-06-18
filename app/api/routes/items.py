from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.item import ItemCreate, ItemRead
from app.services import item_service

router = APIRouter(prefix="/items", tags=["items"])


@router.post("", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: ItemCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ItemRead:
    try:
        item = await item_service.create_item(session, payload)
    except item_service.ItemAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Item with this name already exists",
        ) from exc
    return ItemRead.model_validate(item)


@router.get("", response_model=list[ItemRead])
async def list_items(session: AsyncSession = Depends(get_db_session)) -> list[ItemRead]:
    items = await item_service.list_items(session)
    return [ItemRead.model_validate(item) for item in items]


@router.get("/{item_id}", response_model=ItemRead)
async def get_item(
    item_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> ItemRead:
    try:
        item = await item_service.get_item(session, item_id)
    except item_service.ItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found") from exc
    return ItemRead.model_validate(item)
