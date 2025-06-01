from datetime import datetime, timezone, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from src.utils import save_to_db
from src.settings import EMAIL_ACTIVATION_EXPIRE_MINUTES
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

async def get_email_activation_token(
    db: AsyncSession,
    token: UUID
) -> EmailActivationTokenModel | None:
    result = await db.execute(
        select(EmailActivationTokenModel)
        .options(selectinload(EmailActivationTokenModel.user))
        .where(EmailActivationTokenModel.uuid == token)
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
    return (await save_to_db(db, [user]))[0]

async def create_email_activation_token(
    db: AsyncSession,
    user: UserModel
) -> EmailActivationTokenModel:
    token = EmailActivationTokenModel(user=user)
    return (await save_to_db(db, [token]))[0]

async def activate_user(
    db: AsyncSession,
    email_activation_token: UUID,
    user: UserModel
) -> UserModel:
    token_error = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Invalid or expired activation Token'
    )
    
    token = await get_email_activation_token(db, email_activation_token)
    if token is None:
        raise token_error
    if (datetime.now(timezone.utc) - token.created_at.replace(tzinfo=timezone.utc)) > timedelta(minutes=EMAIL_ACTIVATION_EXPIRE_MINUTES):
        raise token_error
    if token.user_id != user.id:
        raise token_error
    
    user.is_active = True
    await db.delete(token)
    await db.commit()

    return user
