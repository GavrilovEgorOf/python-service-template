from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog
from app.db.session import SessionLocal


async def persist_audit_event(
    *,
    user_id: str,
    request_id: str | None,
    method: str,
    path: str,
    status_code: int,
) -> None:
    if SessionLocal is None:
        return
    async with SessionLocal() as session:
        await _write_audit(session, user_id, request_id, method, path, status_code)


async def _write_audit(
    session: AsyncSession,
    user_id: str,
    request_id: str | None,
    method: str,
    path: str,
    status_code: int,
) -> None:
    session.add(
        AuditLog(
            user_id=user_id,
            request_id=request_id,
            method=method,
            path=path,
            status_code=status_code,
        )
    )
    await session.commit()
