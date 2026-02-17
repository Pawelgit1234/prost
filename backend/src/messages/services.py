from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, exists, and_, delete
from sqlalchemy.orm import selectinload

from src.utils import get_all_objects
from src.auth.models import UserModel
from src.chats.models import ChatModel, UserChatAssociationModel
from src.chats.utils import is_user_in_chat, ensure_user_in_chat_or_403
from src.folders.models import FolderChatAssociationModel, FolderModel
from src.folders.enums import FolderType
from src.messages.models import MessageModel, ReadStatusModel
from src.messages.schemas import MessageSchema
from src.messages.utils import create_read_statuses_for_all_chat_users

async def get_message_or_none(
    db: AsyncSession,
    message_uuid: UUID,
) -> MessageModel | None:
    result = await db.execute(
        select(MessageModel)
        .where(MessageModel.uuid == message_uuid)
        .options(selectinload(MessageModel.read_statuses))
    )
    return result.scalar_one_or_none()

async def get_all_messages(
    db: AsyncSession,
    user: UserModel,
    chat: ChatModel
) -> list[MessageModel]:
    
    ensure_user_in_chat_or_403(user, chat)
    
    messages = await get_all_objects(
        db, MessageModel,
        MessageModel.chat_id == chat.id,
        options=[
            selectinload(MessageModel.read_statuses)
            .selectinload(ReadStatusModel.user)
        ]
    )

    return messages

async def get_read_status_or_none(
    db: AsyncSession,
    user_uuid: UUID,
    message_uuid: UUID
) -> ReadStatusModel | None:
    result = await db.execute(
        select(ReadStatusModel)
        .join(ReadStatusModel.message)
        .join(ReadStatusModel.user)
        .where(
            UserModel.uuid == user_uuid,
            MessageModel.uuid == message_uuid
        )
    )
    return result.scalar_one_or_none()

async def create_message_in_db(
    db: AsyncSession,
    user: UserModel,
    chat: ChatModel,
    content: str
) -> MessageModel | None:
    """
    Creates message in DB and read statuses for all chat users.
    Returns MessageModel or None if user not in chat.
    """
    
    if not is_user_in_chat(user, chat):
        return None
    
    message = MessageModel(
        user_id=user.id,
        chat_id=chat.id,
        content=content,
    )

    db.add(message)
    await db.flush()  # to get message.id

    statuses = create_read_statuses_for_all_chat_users(
        sender_user=user,
        chat=chat,
        message=message,
    )
    db.add_all(statuses)

    await db.commit()
    await db.refresh(message)
    return message
    
async def add_chat_to_new_folder_for_all(
    db: AsyncSession,
    sender_user: UserModel,
    chat: ChatModel,
) -> None:
    """
    Add chat to NEW folder for all chat users except sender
    """

    subq = (
        select(FolderModel.id)
        .join(UserChatAssociationModel,
              UserChatAssociationModel.user_id == FolderModel.user_id)
        .where(
            UserChatAssociationModel.chat_id == chat.id,
            UserChatAssociationModel.user_id != sender_user.id,
            FolderModel.folder_type == FolderType.NEW,
        )
    )

    stmt = insert(FolderChatAssociationModel).from_select(
        ["folder_id", "chat_id"],
        select(
            subq.c.id,
            select(chat.id).scalar_subquery()
        ).where(
            ~exists().where(
                and_(
                    FolderChatAssociationModel.folder_id == subq.c.id,
                    FolderChatAssociationModel.chat_id == chat.id,
                )
            )
        )
    )

    await db.execute(stmt)
    await db.commit()

async def remove_chat_from_new_folder(
    db: AsyncSession,
    user: UserModel,
    chat: ChatModel,
) -> None:
    """Remove chat from user's NEW folder"""

    stmt = delete(FolderChatAssociationModel).where(
        FolderChatAssociationModel.chat_id == chat.id,
        FolderChatAssociationModel.folder_id.in_(
            select(FolderModel.id).where(
                FolderModel.user_id == user.id,
                FolderModel.type == FolderType.NEW,
            )
        )
    )

    await db.execute(stmt)
    await db.commit()

async def read_message(
    db: AsyncSession,
    user: UserModel,
    chat: ChatModel,
    read_status: ReadStatusModel
) -> None:
    
    if not is_user_in_chat(user, chat):
        return None
    
    read_status.is_read = True
    await db.commit()