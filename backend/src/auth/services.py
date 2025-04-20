from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from src.auth.models import UserModel
from src.auth.utils import verify_password

async def get_user_by_username_or_email(
    db: AsyncSession,
    identifier: str
) -> UserModel | None:
    result = await db.execute(
        select(UserModel).where(
            or_(UserModel.username == identifier, UserModel.email == identifier)
        )
    )
    return result.scalar_one_or_none()

async def authenticate_user(db: AsyncSession, identifier: str, password: str) -> UserModel | bool:
    user = await get_user_by_username_or_email(db, identifier)

    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user