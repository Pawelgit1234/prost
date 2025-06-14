from uuid import UUID
import asyncio
import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from redis.asyncio import Redis

from src.settings import REDIS_CHATS_KEY
from src.utils import save_to_db, invalidate_cache
from src.auth.models import UserModel
from src.chats.schemas import CreateChatSchema
from src.chats.models import ChatModel, UserChatAssociationModel
from src.chats.enums import ChatType
from src.folders.models import FolderChatAssociationModel, FolderModel
from src.folders.enums import FolderType

logger = logging.getLogger(__name__)

async def get_chat_or_404(db: AsyncSession, chat_uuid: UUID) -> ChatModel:
    result = await db.execute(
        select(ChatModel)
        .where(ChatModel.uuid == chat_uuid)
        .options(selectinload(ChatModel.user_associations).selectinload(UserChatAssociationModel.user))
    )
    chat = result.scalar_one_or_none()

    if chat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Chat not found')
    
    return chat

async def get_user_or_404(db: AsyncSession, username: str) -> ChatModel:
    from src.auth.services import get_user_by_username_or_email
    user = await get_user_by_username_or_email(db, username)

    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'User not found')
    
    return user

async def create_chat_in_db(
    db: AsyncSession,
    r: Redis,
    current_user: UserModel,
    chat_info: CreateChatSchema
) -> ChatModel:
    from src.folders.services import get_all_folders
    chat = ChatModel(
        chat_type=chat_info.chat_type,
        name=chat_info.name,
        description=chat_info.group_description,
    )
    db.add(chat)
    
    chat_assoc = UserChatAssociationModel(
        user=current_user,
        chat=chat
    )
    db.add(chat_assoc)

    folders = await get_all_folders(db, current_user)
    all_folder = None
    chats_folder = None
    groups_folder = None
    for folder in folders:
        match folder.folder_type:
            case FolderType.ALL:
                all_folder = folder
            case FolderType.CHATS:
                chats_folder = folder
            case FolderType.GROUPS:
                groups_folder = folder
    
    all_folder_assoc = FolderChatAssociationModel(folder=all_folder, chat=chat)
    db.add(all_folder_assoc)

    await invalidate_cache(r, REDIS_CHATS_KEY, all_folder.folder_type)

    if chat_info.chat_type == ChatType.NORMAL:
        chats_folder_assoc = FolderChatAssociationModel(folder=chats_folder, chat=chat)
        other_user = await get_user_or_404(db, chat_info.name)

        other_folders = await get_all_folders(db, other_user)
        for folder in other_folders:
            match folder.folder_type:
                case FolderType.ALL:
                    other_all_folder = folder
                case FolderType.CHATS:
                    other_chats_folder = folder

        other_all_folder_assoc = FolderChatAssociationModel(folder=other_all_folder, chat=chat)
        other_chats_folder_assoc = FolderChatAssociationModel(folder=other_chats_folder, chat=chat)

        other_chat_assoc = UserChatAssociationModel(
            user=other_user,
            chat=chat
        )
        db.add_all(other_chat_assoc, chats_folder_assoc, other_chats_folder_assoc, other_all_folder_assoc)
        await invalidate_cache(r, REDIS_CHATS_KEY, chats_folder.folder_type)
        await invalidate_cache(r, REDIS_CHATS_KEY, other_all_folder.folder_type)
        await invalidate_cache(r, REDIS_CHATS_KEY, other_chats_folder.folder_type)
    elif chat_info.chat_type == ChatType.GROUP:
        group_folder_assoc = FolderChatAssociationModel(folder=groups_folder, chat=chat)
        db.add(group_folder_assoc)
        await invalidate_cache(r, REDIS_CHATS_KEY, groups_folder.folder_type)
    
    await db.commit()
    logger.info(f"Chat '{chat.name}' was created by '{current_user.username}'")
    return chat

async def delete_chat_in_db(
    db: AsyncSession,
    r: Redis,
    user: UserModel,
    chat_uuid: UUID
) -> list[UserModel]:
    chat = await get_chat_or_404(db, chat_uuid)
    users = [assoc.user for assoc in chat.user_associations]

    tasks = [invalidate_cache(r, REDIS_CHATS_KEY, folder.uuid) for folder in chat.folder_associations]
    await asyncio.gather(*tasks)

    if user not in users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You must be in the group, if you want delete it'
        )

    await db.delete(chat)
    await db.commit()
    logger.info(f"Chat '{chat.name}' was deleted'")
    return users

async def quit_group_in_db(
    db: AsyncSession,
    r: Redis,
    current_user: UserModel,
    chat_uuid: UUID
) -> None:
    chat = await get_chat_or_404(db, chat_uuid)
    tasks = [invalidate_cache(r, REDIS_CHATS_KEY, folder.uuid) for folder in chat.folder_associations]
    await asyncio.gather(*tasks)

    # goes trough all users
    for assoc in chat.user_associations:
        if assoc.user_id == current_user.id:
            await db.delete(assoc)
            logger.info(f"'{current_user.username}' quitted chat '{chat.name}'")
            break
    
    stmt = (
        delete(FolderChatAssociationModel)
        .where(
            FolderChatAssociationModel.chat_id == chat.id,
            FolderChatAssociationModel.folder_id.in_(
                select(FolderModel.id).where(FolderModel.user_id == current_user.id)
            )
        )
    )
    await db.execute(stmt)
    await db.commit()

async def add_user_to_group_in_db(
    db: AsyncSession,
    r: Redis,
    group_uuid: UUID,
    username: str,
    current_user: UserModel,
) -> UserModel:
    from src.folders.services import get_all_folders
    # two requests 'parallel' are faster
    chat, user = await asyncio.gather(
        get_chat_or_404(db, group_uuid),
        get_user_or_404(db, username)
    )
    
    if current_user not in chat.user_associations:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You must be in the group, if you want add someone'
        )
    
    chat_association = UserChatAssociationModel(user=user, chat=chat)

    folders = await get_all_folders(db, user)
    all_folder = None
    group_folder = None
    for folder in folders:
        match folder.folder_type:
            case FolderType.ALL:
                all_folder = folder
            case FolderType.GROUPS:
                group_folder = folder

    await invalidate_cache(r, REDIS_CHATS_KEY, all_folder.folder_type)
    await invalidate_cache(r, REDIS_CHATS_KEY, group_folder.folder_type)

    all_folder_assoc = FolderChatAssociationModel(folder=all_folder, chat=chat)
    group_folder_assoc = FolderChatAssociationModel(folder=group_folder, chat=chat)

    await save_to_db(db, [chat_association, all_folder_assoc, group_folder_assoc])
    logger.info(f"'{user.username}' joined chat '{chat.name}'")
    return user
