from typing import Iterable, Sequence

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeMeta, Load
from sqlalchemy import select, ClauseElement
from fastapi import HTTPException, status

async def save_to_db(db: AsyncSession, instances: Iterable[object]):
    db.add_all(instances)
    await db.commit()
    for obj in instances:
        await db.refresh(obj)
    return instances

async def get_object_or_404(
    db: AsyncSession,
    model: type[DeclarativeMeta],
    condition: ClauseElement,
    *,
    options: Sequence[Load] | None = None,
    detail: str = "Object not found"
) -> DeclarativeMeta:
    stmt = select(model).where(condition)

    if options:
        stmt = stmt.options(*options)

    result = await db.execute(stmt)
    obj = result.scalar_one_or_none()

    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail)
    
    return obj

async def invalidate_cache(r: Redis, key: str, *args) -> None:
    key = key.format(*args)
    await r.delete(key)
