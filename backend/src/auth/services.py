from datetime import datetime, timezone, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from src.utils import save_to_db, get_object_or_404
from src.settings import EMAIL_ACTIVATION_EXPIRE_MINUTES
from src.auth.models import UserModel, EmailActivationTokenModel
from src.auth.schemas import UserRegisterSchema
from src.auth.utils import verify_password, get_password_hash
from src.folders.services import create_folder_in_db
from src.folders.enums import FolderType

async def get_user_or_none(db: AsyncSession, email: str) -> UserModel | None:
    result = await db.execute(select(UserModel).where(UserModel.email == email))
    return result.scalar_one_or_none()

async def authenticate_user(
    db: AsyncSession,
    identifier: str,
    password: str
) -> UserModel | bool:
    user = await get_object_or_404(
        db, UserModel,
        or_(UserModel.username == identifier, UserModel.email == identifier),
        detail='User not found'
    )

    if not verify_password(password, user.password):
        return False
    return user

async def create_user(db: AsyncSession, user_data: UserRegisterSchema) -> UserModel:
    try:
        user = UserModel(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            username=user_data.username,
            description=user_data.description,
            email=user_data.email,
            password=get_password_hash(user_data.password)
        )
        user = (await save_to_db(db, [user]))[0]

        # creates all folder types (except custom)
        await create_folder_in_db(db=db, user=user, folder_type=FolderType.ALL)
        await create_folder_in_db(db=db, user=user, folder_type=FolderType.CHATS)
        await create_folder_in_db(db=db, user=user, folder_type=FolderType.GROUPS)
        await create_folder_in_db(db=db, user=user, folder_type=FolderType.NEW)
        
        return user
    except IntegrityError as e:
        await db.rollback()

        if 'ix_users_email' in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='Email already registered'
            )
        elif 'ix_users_username' in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='Username already taken'
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='User registration failed'
            )

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
    
    token = await get_object_or_404(
        db, EmailActivationTokenModel,
        EmailActivationTokenModel.uuid == email_activation_token,
        options=[selectinload(EmailActivationTokenModel.user)],
        detail='Email activation token not found'
    )

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
