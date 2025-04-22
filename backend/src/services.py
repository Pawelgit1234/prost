from sqlalchemy.ext.asyncio import AsyncSession

async def save_to_db(db: AsyncSession, instance):
    db.add(instance)
    await db.commit()
    await db.refresh(instance)
    return instance
