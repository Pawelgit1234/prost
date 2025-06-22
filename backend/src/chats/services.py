from uuid import UUID
import asyncio
import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from redis.asyncio import Redis

from src.settings import REDIS_CHATS_KEY
from src.utils import save_to_db, invalidate_cache, get_object_or_404
from src.auth.models import UserModel
from src.chats.schemas import CreateChatSchema
from src.chats.models import ChatModel, UserChatAssociationModel
from src.chats.enums import ChatType
from src.chats.utils import group_folders_by_type, invalidate_chat_cache
from src.folders.models import FolderChatAssociationModel, FolderModel
from src.folders.enums import FolderType

logger = logging.getLogger(__name__)

# is shorter
async def _get_chat_or_404(db: AsyncSession, chat_uuid: UUID) -> ChatModel:
    return await get_object_or_404(
        db, ChatModel, ChatModel.uuid == chat_uuid, detail='Chat not found',
        options=[
            selectinload(ChatModel.user_associations)
            .selectinload(UserChatAssociationModel.user),
            selectinload(ChatModel.folder_associations)
            .selectinload(FolderChatAssociationModel.folder)
        ]
    )

async def create_chat_in_db(
    db: AsyncSession,
    r: Redis,
    current_user: UserModel,
    chat_info: CreateChatSchema
) -> ChatModel:
    from src.folders.services import get_folders_list

    chat = ChatModel(
        chat_type=chat_info.chat_type,
        name=chat_info.name,
        description=chat_info.group_description,
    )
    db.add(chat)
    
    chat_assoc = UserChatAssociationModel(user=current_user, chat=chat)
    db.add(chat_assoc)

    folders = group_folders_by_type(await get_folders_list(db, current_user))
    all_folder_assoc = FolderChatAssociationModel(folder=folders[FolderType.ALL], chat=chat)
    db.add(all_folder_assoc)

    await invalidate_cache(r, REDIS_CHATS_KEY, folders[FolderType.ALL].uuid, current_user.uuid)

    if chat_info.chat_type == ChatType.NORMAL:
        chats_folder_assoc = FolderChatAssociationModel(folder=folders[FolderType.CHATS], chat=chat)
        other_user = await get_object_or_404(
            db, UserModel, UserModel.username == chat_info.name,
            detail='User not found'
        )

        # add chat in folders from other users
        other_folders = group_folders_by_type(await get_folders_list(db, other_user))
        other_all_folder_assoc = FolderChatAssociationModel(folder=other_folders[FolderType.ALL], chat=chat)
        other_chats_folder_assoc = FolderChatAssociationModel(folder=other_folders[FolderType.CHATS], chat=chat)
        other_chat_assoc = UserChatAssociationModel(user=other_user, chat=chat)
        db.add_all([other_chat_assoc, chats_folder_assoc, other_chats_folder_assoc, other_all_folder_assoc])
        
        await invalidate_chat_cache(
            r,
            folders[FolderType.CHATS],
            other_folders[FolderType.ALL],
            other_folders[FolderType.CHATS],
            user=current_user
        )
    elif chat_info.chat_type == ChatType.GROUP:
        group_folder_assoc = FolderChatAssociationModel(folder=folders[FolderType.GROUPS], chat=chat)
        db.add(group_folder_assoc)
        await invalidate_cache(r, REDIS_CHATS_KEY, folders[FolderType.GROUPS].uuid, current_user.uuid)
    
    # commit and flush
    chat = (await save_to_db(db, [chat]))[0]

    logger.info(f"Chat '{chat.name}' created by '{current_user.username}'")
    return chat

async def delete_chat_in_db(
    db: AsyncSession,
    r: Redis,
    user: UserModel,
    chat_uuid: UUID
) -> None: 
    chat = await _get_chat_or_404(db, chat_uuid)
    user_ids = [assoc.user_id for assoc in chat.user_associations]

    folders = [assoc.folder for assoc in chat.folder_associations]
    await invalidate_chat_cache(r, *folders, user=user)

    if user.id not in user_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Only group members can delete this chat'
        )

    await db.delete(chat)
    await db.commit()
    logger.info(f"Chat '{chat.name}' deleted'")

async def quit_group_in_db(
    db: AsyncSession,
    r: Redis,
    current_user: UserModel,
    chat_uuid: UUID
) -> None:
    chat = await _get_chat_or_404(db, chat_uuid)
    folders = [assoc.folder for assoc in chat.folder_associations]
    await invalidate_chat_cache(r, *folders, user=current_user)

    # goes trough all users
    for assoc in chat.user_associations:
        if assoc.user_id == current_user.id:
            await db.delete(assoc)
            logger.info(f"'{current_user.username}' quit group '{chat.name}'")
            break
    
    await db.execute(
        delete(FolderChatAssociationModel)
        .where(
            FolderChatAssociationModel.chat_id == chat.id,
            FolderChatAssociationModel.folder_id.in_(
                select(FolderModel.id).where(FolderModel.user_id == current_user.id)
            )
        )
    )
    await db.commit()

async def add_user_to_group_in_db(
    db: AsyncSession,
    r: Redis,
    group_uuid: UUID,
    username: str,
    current_user: UserModel,
) -> None:
    from src.folders.services import get_folders_list
    # two requests 'parallel' are faster
    group, user = await asyncio.gather(
        _get_chat_or_404(db, group_uuid),
        get_object_or_404(
            db, UserModel, UserModel.username == username,
            detail='User not found'
        )
    )
    
    user_ids = [assoc.user_id for assoc in group.user_associations]
    if current_user.id not in user_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Only group members can add new users'
        )
    
    # checks if user already is member of the group
    existing = await db.execute(
        select(UserChatAssociationModel)
        .where(UserChatAssociationModel.user_id == user.id,
            UserChatAssociationModel.chat_id == group.id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of the group"
        )

    folders = group_folders_by_type(await get_folders_list(db, user))
    await invalidate_chat_cache(r, folders[FolderType.ALL], folders[FolderType.GROUPS], user=user)

    chat_association = UserChatAssociationModel(user=user, chat=group)
    all_folder_assoc = FolderChatAssociationModel(folder=folders[FolderType.ALL], chat=group)
    group_folder_assoc = FolderChatAssociationModel(folder=folders[FolderType.GROUPS], chat=group)
    db.add_all([chat_association, all_folder_assoc, group_folder_assoc])
    await db.commit()

    logger.info(f"'{user.username}' join group '{group.name}'")
