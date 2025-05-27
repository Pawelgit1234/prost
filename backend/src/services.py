from typing import Iterable

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def save_to_db(db: AsyncSession, objects: Iterable):
    db.add_all(objects)
    await db.commit()
    for obj in objects:
        await db.refresh(obj)
    return objects

async def invalidate_cache(r: Redis, key: str, *args) -> None:
    key = key.format(*args)
    await r.delete(key)