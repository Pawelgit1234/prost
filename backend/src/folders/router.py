from uuid import UUID
from typing import Annotated
import logging
import json

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from redis.asyncio import Redis

from src.settings import REDIS_FOLDERS_KEY, REDIS_CHATS_KEY, \
    REDIS_CACHE_EXPIRE_SECONDS
from src.database import get_db, get_redis
from src.utils import invalidate_cache, get_object_or_404, wrap_list_response
from src.dependencies import get_active_current_user
from src.auth.models import UserModel
from src.chats.models import ChatModel
from src.folders.models import FolderModel
from src.folders.schemas import CreateFolderSchema, FolderSchema
from src.folders.services import create_folder_in_db, delete_folder_in_db, \
    get_folders_list, add_chat_to_folder, delete_chat_from_folder, \
    pin_chat_in_folder, get_folder_chat_assoc_or_404
from src.folders.utils import folder_model_to_schema
    
logger = logging.getLogger(__name__)

router = APIRouter(prefix='/folders', tags=['folders'])

@router.get('/')
async def get_all_folders(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
):
    redis_key = REDIS_FOLDERS_KEY.format(current_user.uuid)
    if data := await r.get(redis_key):
        return json.loads(data)

    folder_models = await get_folders_list(db, current_user)
    folders = [
        folder_model_to_schema(folder).model_dump()
        for folder in folder_models
    ]
    data = wrap_list_response(folders)

    await r.set(
        redis_key,
        json.dumps(data, default=str),
        REDIS_CACHE_EXPIRE_SECONDS
    )

    return data

# @router.get('/{folder_uuid}/')
# async def get_chats_from_folder(
#     db: Annotated[AsyncSession, Depends(get_db)],
#     r: Annotated[Redis, Depends(get_redis)],
#     current_user: Annotated[UserModel, Depends(get_active_current_user)],
#     folder_uuid: UUID
# ):
#     redis_key = REDIS_CHATS_KEY.format(folder_uuid, current_user.uuid)
#     if data := await r.get(redis_key):
#         return json.loads(data)
# 
#     chat_models = await get_chats_list_from_folder(db, current_user, folder_uuid)
#     chats = serialize_model_list(chat_models, ChatSchema)
#     data = wrap_list_response(chats)
# 
#     await r.set(
#         redis_key,
#         json.dumps(data),
#         REDIS_CACHE_EXPIRE_SECONDS
#     )
# 
#    return data

# only for custom
@router.post('/')
async def create_folder(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    folder_info: CreateFolderSchema,
):
    folder = await create_folder_in_db(db, current_user, folder_info)
    await invalidate_cache(r, REDIS_FOLDERS_KEY, current_user.uuid)
    logger.info(f'Folder {folder.name} created by {current_user.username}')
    return FolderSchema.model_validate(folder)

# only for custom
@router.delete('/{folder_uuid}/')
async def delete_folder(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    folder_uuid: UUID
):
    folder = await get_object_or_404(
        db, FolderModel, FolderModel.uuid == folder_uuid,
        detail='Folder not found'
    )

    await delete_folder_in_db(db, current_user, folder)
    await invalidate_cache(r, REDIS_FOLDERS_KEY, current_user.uuid)
    return {'success': True}

# only for custom
@router.put('/add_chat')
async def add_chat(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    chat_uuid: UUID,
    folder_uuid: UUID
):
    folder = await get_object_or_404(
        db, FolderModel, FolderModel.uuid == folder_uuid, detail='Folder not found'
    )
    chat = await get_object_or_404(
        db, ChatModel, ChatModel.uuid == chat_uuid, detail='Chat not found',
        options=[selectinload(ChatModel.user_associations)]
    )
    await add_chat_to_folder(db, current_user, folder, chat)
    await invalidate_cache(r, REDIS_CHATS_KEY, current_user.uuid)
    logger.info(f'Chat added to folder {folder.name} by {current_user.username}')
    return {'success': True}

# only for custom
@router.put('/delete_chat')
async def delete_chat(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    chat_uuid: UUID,
    folder_uuid: UUID
):
    assoc = await get_folder_chat_assoc_or_404(db, current_user, folder_uuid, chat_uuid)
    await delete_chat_from_folder(db, current_user, assoc)
    await invalidate_cache(r, REDIS_CHATS_KEY, current_user.uuid)
    logger.info(f'Chat deleted from folder {assoc.folder.name} by {current_user.username}')
    return {'success': True}

# toggles the 'is_pinned' field
@router.put('{chat_uuid}/pin')
async def pin_chat(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    chat_uuid: UUID,
    folder_uuid: UUID
):
    assoc = await get_folder_chat_assoc_or_404(db, current_user, folder_uuid, chat_uuid)
    is_pinned = await pin_chat_in_folder(db, current_user, assoc)
    await invalidate_cache(r, REDIS_CHATS_KEY, current_user.uuid)
    logger.info(f'Chat pinned in folder {assoc.folder.name} by {current_user.username}')
    return {'is_pinned': is_pinned}
