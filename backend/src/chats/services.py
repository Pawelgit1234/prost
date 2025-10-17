from uuid import UUID
import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload, aliased
from redis.asyncio import Redis
from elasticsearch import AsyncElasticsearch

from src.utils import save_to_db, get_object_or_404
from src.auth.models import UserModel
from src.messages.models import MessageModel
from src.chats.schemas import CreateChatSchema
from src.chats.models import ChatModel, UserChatAssociationModel
from src.chats.enums import ChatType
from src.chats.utils import group_folders_by_type, ensure_user_in_chat_or_403,\
    update_group_members_in_elastic, ensure_no_normal_chat_or_403, chat_and_message_model_to_schema,\
    other_user_to_chat_schema
from src.folders.models import FolderChatAssociationModel, FolderModel
from src.folders.enums import FolderType

logger = logging.getLogger(__name__)

async def get_all_chats_with_last_message(
    db: AsyncSession, user: UserModel
) -> list[tuple[ChatModel, MessageModel]]:

    # subquery: last message for every chat
    last_message_subq = (
        select(MessageModel.id)
        .where(MessageModel.chat_id == ChatModel.id)
        .order_by(MessageModel.created_at.desc())
        .limit(1)
        .correlate(ChatModel)
        .scalar_subquery()
    )

    LastMessage = aliased(MessageModel)

    stmt = (
        select(
            ChatModel,
            LastMessage
        )
        .join(UserChatAssociationModel, ChatModel.id == UserChatAssociationModel.chat_id)
        .outerjoin(LastMessage, LastMessage.id == last_message_subq)
        .where(UserChatAssociationModel.user_id == user.id)
        .order_by(ChatModel.created_at.desc())
        .options(
            selectinload(ChatModel.user_associations)
            .selectinload(UserChatAssociationModel.user)
        )
    )

    result = await db.execute(stmt)
    rows = result.all()
    return rows

async def get_chat_schemas(db: AsyncSession, user: UserModel):
    chats = await get_all_chats_with_last_message(db, user)
    schemas = []

    for chat, last_message in chats:
        if chat.chat_type == ChatType.GROUP:
            schemas.append(chat_and_message_model_to_schema(chat, last_message))
        else:
            schemas.append(other_user_to_chat_schema(user, chat, last_message))

    return schemas

# is shorter in that way
async def get_chat_or_404(db: AsyncSession, chat_uuid: UUID) -> ChatModel:
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
    current_user: UserModel,
    chat_info: CreateChatSchema
) -> ChatModel:
    from src.folders.services import get_folders_list

    chat = ChatModel(
        chat_type=chat_info.chat_type,
        name=None if chat_info.chat_type == ChatType.NORMAL else chat_info.name,
        description=chat_info.group_description,
    )
    db.add(chat)
    
    chat_assoc = UserChatAssociationModel(user=current_user, chat=chat)
    db.add(chat_assoc)

    folders = group_folders_by_type(await get_folders_list(db, current_user))
    all_folder_assoc = FolderChatAssociationModel(folder=folders[FolderType.ALL], chat=chat)
    db.add(all_folder_assoc)

    if chat_info.chat_type == ChatType.NORMAL:
        chats_folder_assoc = FolderChatAssociationModel(folder=folders[FolderType.CHATS], chat=chat)
        other_user = await get_object_or_404(
            db, UserModel, UserModel.username == chat_info.name,
            detail='User not found',
            options=[selectinload(UserModel.chat_associations)]
        )
        await ensure_no_normal_chat_or_403(db, current_user, other_user)

        # add chat in folders from other users
        other_folders = group_folders_by_type(await get_folders_list(db, other_user))
        other_all_folder_assoc = FolderChatAssociationModel(folder=other_folders[FolderType.ALL], chat=chat)
        other_chats_folder_assoc = FolderChatAssociationModel(folder=other_folders[FolderType.CHATS], chat=chat)
        other_chat_assoc = UserChatAssociationModel(user=other_user, chat=chat)
        db.add_all([other_chat_assoc, chats_folder_assoc, other_chats_folder_assoc, other_all_folder_assoc])
        
    elif chat_info.chat_type == ChatType.GROUP:
        group_folder_assoc = FolderChatAssociationModel(folder=folders[FolderType.GROUPS], chat=chat)
        db.add(group_folder_assoc)

    # commit and flush
    chat = (await save_to_db(db, [chat]))[0]
    # loads user and folder associations
    chat = await get_chat_or_404(db, chat.uuid)

    return chat

async def delete_chat_in_db(
    db: AsyncSession,
    user: UserModel,
    chat: ChatModel
) -> None: 
    ensure_user_in_chat_or_403(user, chat, 'Only group members can delete this chat')

    # folders = [assoc.folder for assoc in chat.folder_associations]
    # await invalidate_chat_cache(r, *folders, user=user)

    await db.delete(chat)
    await db.commit()

async def quit_group_in_db(
    db: AsyncSession,
    r: Redis,
    es: AsyncElasticsearch,
    current_user: UserModel,
    group: ChatModel
) -> None:
    # folders = [assoc.folder for assoc in group.folder_associations]
    # await invalidate_chat_cache(r, *folders, user=current_user)

    # quit group
    for assoc in group.user_associations:
        if assoc.user_id == current_user.id:
            await db.delete(assoc)
            logger.info(f"'{current_user.username}' quit group '{group.name}'")
            break
    
    # remove from the folder
    await db.execute(
        delete(FolderChatAssociationModel)
        .where(
            FolderChatAssociationModel.chat_id == group.id,
            FolderChatAssociationModel.folder_id.in_(
                select(FolderModel.id).where(FolderModel.user_id == current_user.id)
            )
        )
    )
    await db.commit()

    await update_group_members_in_elastic(es, group)

async def add_user_to_group_in_db(
    db: AsyncSession,
    es: AsyncElasticsearch,
    group: ChatModel,
    user: UserModel,
) -> ChatModel:
    """ Adds user to group """
    from src.folders.services import get_folders_list

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

    chat_association = UserChatAssociationModel(user=user, chat=group)
    all_folder_assoc = FolderChatAssociationModel(folder=folders[FolderType.ALL], chat=group)
    group_folder_assoc = FolderChatAssociationModel(folder=folders[FolderType.GROUPS], chat=group)
    db.add_all([chat_association, all_folder_assoc, group_folder_assoc])
    await db.commit()

    await update_group_members_in_elastic(es, group)
    return group

async def user_add_user_to_group_in_db(
    db: AsyncSession,
    es: AsyncElasticsearch,
    group: ChatModel,
    other_user: UserModel,
    user: UserModel
) -> ChatModel:
    """ User add other user into group """

    ensure_user_in_chat_or_403(user, group, 'Only group members can add new users')
    group = await add_user_to_group_in_db(db, es, group, other_user)
    logger.info(f"'{other_user.username}' added to group '{group.name}' by {user.username}")

    return group
