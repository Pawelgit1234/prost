from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from src.services import save_to_db
from src.auth.models import UserModel, EmailActivationTokenModel
from src.auth.schemas import UserRegisterSchema
from src.auth.utils import verify_password, get_password_hash

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

async def authenticate_user(
    db: AsyncSession,
    identifier: str,
    password: str
) -> UserModel | bool:
    user = await get_user_by_username_or_email(db, identifier)

    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

async def create_user(db: AsyncSession, user_data: UserRegisterSchema) -> UserModel:
    user = UserModel(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        username=user_data.username,
        description=user_data.description,
        email=user_data.email,
        password=get_password_hash(user_data.password)
    )
    return await save_to_db(db, user)

async def create_email_activation_token(db: AsyncSession, user: UserModel) -> EmailActivationTokenModel:
    token = EmailActivationTokenModel(user=user)
    return await save_to_db(db, token)
