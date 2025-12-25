import asyncio
import logging
from typing import Annotated
from uuid import UUID
import json

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from elasticsearch import AsyncElasticsearch

from src.folders.services import get_folder_chat_assoc_or_404
from src.chats.services import create_chat_in_db, delete_chat_in_db,\
    quit_group_in_db, user_add_user_to_group_in_db, get_chat_or_404, get_chat_schemas, \
    pin_chat_in_folder, set_chat_folder_in_db
from src.chats.models import ChatModel
from src.chats.utils import get_group_users_uuids
from src.chats.schemas import CreateChatSchema, ChatSchema, SetChatFoldersSchema
from src.dependencies import get_active_current_user
from src.utils import get_object_or_404, invalidate_cache, wrap_list_response
from src.settings import ELASTIC_CHATS_INDEX_NAME, REDIS_CHATS_KEY, REDIS_CACHE_EXPIRE_SECONDS, \
    REDIS_FOLDERS_KEY
from src.auth.models import UserModel
from src.database import get_db, get_redis, get_es

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/chats', tags=['chats'])

@router.get('/')
async def get_all_chats(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
):
    redis_key = REDIS_CHATS_KEY.format(current_user.uuid)
    if data := await r.get(redis_key):
        return json.loads(data)

    chats_schemas = await get_chat_schemas(db, current_user)
    chats = [chat.model_dump() for chat in chats_schemas]
    data = wrap_list_response(chats)

    await r.set(
        redis_key,
        json.dumps(data, default=str),
        REDIS_CACHE_EXPIRE_SECONDS
    )

    return data

@router.post('/')
async def create_chat(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    chat_info: CreateChatSchema
):
    chat = await create_chat_in_db(db, r, current_user, chat_info)
    await invalidate_cache(r, REDIS_CHATS_KEY, current_user.uuid)
    await es.index(
        index=ELASTIC_CHATS_INDEX_NAME,
        id=str(chat.uuid),
        documene={
            "chat_type": chat.chat_type.value,
            "name": chat.name,
            "description": chat.description,
            "avatar": None,
            "members": get_group_users_uuids(chat),
            "is_visible": chat.is_visible,
        }
    )
    logger.info(f"Chat '{chat.name}' created by '{current_user.username}'")
    return ChatSchema.model_validate(chat)

@router.delete('/{chat_uuid}')
async def delete_chat(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    chat_uuid: UUID
):
    chat = await get_chat_or_404(db, chat_uuid)
    await delete_chat_in_db(db, current_user, chat)
    await invalidate_cache(r, REDIS_CHATS_KEY, current_user.uuid)
    await es.delete(index=ELASTIC_CHATS_INDEX_NAME, id=str(chat_uuid))

    logger.info(f"Chat '{chat.name}' deleted by '{current_user.username}'")
    return {'success': True}

# you can quit a group without deleting it
@router.delete('/{group_uuid}/quit')
async def quit_group(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    group_uuid: UUID
):
    group = await get_chat_or_404(db, group_uuid)
    await quit_group_in_db(db, es, current_user, group)
    await invalidate_cache(r, REDIS_CHATS_KEY, current_user.uuid)

    logger.info(f"'{current_user.username}' quit group '{group.name}'")
    return {'success': True}

@router.post('{group_uuid}/add_user')
async def add_user_to_group(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    group_uuid: UUID,
    username: str
):
    # two requests 'parallel' are faster
    group, other_user = await asyncio.gather(
        get_chat_or_404(db, group_uuid),
        get_object_or_404(
            db, UserModel, UserModel.username == username,
            detail='User not found'
        )
    )

    group = await user_add_user_to_group_in_db(db, es, group, other_user, current_user)
    await invalidate_cache(r, REDIS_CHATS_KEY, current_user.uuid)
    return {'success': True}

# # only for custom
# @router.put('/add_chat')
# async def add_chat(
#     db: Annotated[AsyncSession, Depends(get_db)],
#     r: Annotated[Redis, Depends(get_redis)],
#     current_user: Annotated[UserModel, Depends(get_active_current_user)],
#     chat_uuid: UUID,
#     folder_uuid: UUID
# ):
#     folder = await get_object_or_404(
#         db, FolderModel, FolderModel.uuid == folder_uuid, detail='Folder not found'
#     )
#     chat = await get_object_or_404(
#         db, ChatModel, ChatModel.uuid == chat_uuid, detail='Chat not found',
#         options=[selectinload(ChatModel.user_associations)]
#     )
#     await add_chat_to_folder(db, current_user, folder, chat)
#     await invalidate_cache(r, REDIS_FOLDERS_KEY, current_user.uuid)
#     logger.info(f'Chat added to folder {folder.name} by {current_user.username}')
#     return {'success': True}
# 
# # only for custom
# @router.put('/delete_chat_from_folder')
# async def delete_chat_from_folder(
#     db: Annotated[AsyncSession, Depends(get_db)],
#     r: Annotated[Redis, Depends(get_redis)],
#     current_user: Annotated[UserModel, Depends(get_active_current_user)],
#     chat_uuid: UUID,
#     folder_uuid: UUID
# ):
#     """ Removes chat from folder """
#     assoc = await get_folder_chat_assoc_or_404(db, current_user, folder_uuid, chat_uuid)
#     await delete_chat_from_folder(db, current_user, assoc)
#     await invalidate_cache(r, REDIS_FOLDERS_KEY, current_user.uuid)
#     logger.info(f'Chat deleted from folder {assoc.folder.name} by {current_user.username}')
#     return {'success': True}

# only for custom folders
@router.put('/{chat_uuid}/folders')
async def set_chat_folders(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    chat_uuid: UUID,
    folder_uuids: SetChatFoldersSchema
):
    chat = await get_chat_or_404(db, chat_uuid)
    await set_chat_folder_in_db(db, current_user, chat, folder_uuids.folder_uuids)
    await invalidate_cache(r, REDIS_FOLDERS_KEY, current_user.uuid)
    logger.info(f'Folders of the chat {chat_uuid} were setted')
    return {'success': True}

# toggles the 'is_pinned' field
@router.put('/{chat_uuid}/folders/{folder_uuid}/pin')
async def pin_chat(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    chat_uuid: UUID,
    folder_uuid: UUID
):
    assoc = await get_folder_chat_assoc_or_404(db, current_user, folder_uuid, chat_uuid)
    is_pinned = await pin_chat_in_folder(db, assoc)
    await invalidate_cache(r, REDIS_FOLDERS_KEY, current_user.uuid)
    logger.info(f'Chat pinned in folder {assoc.folder.name} by {current_user.username}')
    return {'is_pinned': is_pinned}
