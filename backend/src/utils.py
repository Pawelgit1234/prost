from typing import Iterable

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def save_to_db(db: AsyncSession, instances: Iterable[object]):
    db.add_all(instances)
    await db.commit()
    for obj in instances:
        await db.refresh(obj)
    return instances

async def invalidate_cache(r: Redis, key: str, *args) -> None:
    key = key.format(*args)
    await r.delete(key)