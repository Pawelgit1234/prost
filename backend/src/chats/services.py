from uuid import UUID
import asyncio
import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.services import save_to_db
from src.auth.models import UserModel
from src.auth.services import get_user_by_username_or_email
from src.chats.schemas import CreateChatSchema, ChatSchema
from src.chats.models import ChatModel, UserChatAssociationModel

logger = logging.getLogger(__name__)

async def get_chat_or_404(db: AsyncSession, chat_uuid: UUID) -> ChatModel:
    result = await db.execute(
        select(ChatModel).where(ChatModel.uuid == chat_uuid)
    )
    chat = result.scalar_one_or_none()

    if chat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Chat not found')

async def get_user_or_404(db: AsyncSession, username: str) -> ChatModel:
    user = get_user_by_username_or_email(db, username)

    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'User not found')

async def get_chat_list(db: AsyncSession, current_user: UserModel) -> list[ChatSchema]:
    result = await db.execute(
        select(ChatModel)
        .join(ChatModel.user_associations)
        .where(UserChatAssociationModel.user_id == current_user.id)
        .options(selectinload(ChatModel.user_associations))
    )
    chats = result.scalars().all()
    
    schemas = []
    for chat in chats:
        # goes trough all users
        for assoc in chat.user_associations:
            if assoc.user_id == current_user.id:
                schemas.append(ChatSchema.model_validate({
                    **chat.__dict__,
                    'is_pinned': assoc.is_pinned
                }))
                break

    return schemas

async def create_chat_in_db(
    db: AsyncSession,
    current_user: UserModel,
    chat_info: CreateChatSchema
) -> ChatModel:
    chat = ChatModel(
        chat_type=chat_info.chat_type,
        name=chat_info.name,
        description=chat_info.group_description,
    )
    chat_association = UserChatAssociationModel(
        user=current_user,
        chat=chat
    )
    chat = await save_to_db(db, [chat, chat_association])[0]
    logger.info(f"Chat '{chat.name}' was created by '{current_user.username}'")
    return chat

async def delete_chat_in_db(
    db: AsyncSession,
    chat_uuid: UUID
) -> list[UserModel]:
    chat = await get_chat_or_404(db, chat_uuid)
    users = [assoc.user for assoc in chat.user_associations]
    await db.delete(chat)
    await db.commit()
    logger.info(f"Chat '{chat.name}' was deleted'")
    return users

async def quit_group_in_db(
    db: AsyncSession,
    current_user: UserModel,
    chat_uuid: UUID
) -> None:
    chat = await get_chat_or_404(db, chat_uuid)
    
    # goes trough all users
    for assoc in chat.user_associations:
        if assoc.user_id == current_user.id:
            await db.delete(assoc)
            await db.commit()
            logger.info(f"'{current_user.username}' quitted chat '{chat.name}'")
            break

async def add_user_to_group_in_db(
    db: AsyncSession,
    group_uuid: UUID,
    username: str
) -> UserModel:
    # two requests 'parallel' are faster
    chat, user = await asyncio.gather(
        get_chat_or_404(db, group_uuid),
        get_user_or_404(db, username)
    )
    
    chat_association = UserChatAssociationModel(
        user=user,
        chat=chat
    )

    await save_to_db(db, [chat_association])
    logger.info(f"'{user.username}' joined chat '{chat.name}'")
    return user

# True -> chat was pinned up
# False -> chat was unpinned
async def pin_chat_in_db(
    db: AsyncSession,
    current_user: UserModel,
    chat_uuid: UUID
) -> bool:
    result = await db.execute(
        select(UserChatAssociationModel)
        .join(ChatModel)
        .where(ChatModel.uuid == chat_uuid)
        .where(UserChatAssociationModel.user_id == current_user.id)
    )
    assoc = result.scalar_one_or_none()

    if assoc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Association not found')
    
    assoc.is_pinned = not assoc.is_pinned
    await db.commit()
    return assoc.is_pinned
