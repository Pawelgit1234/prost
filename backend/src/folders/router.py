from uuid import UUID
from typing import Annotated
import json

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from src.database import get_db, get_redis
from src.dependencies import get_active_current_user
from src.auth.models import UserModel
from src.chats.schemas import ChatSchema
from src.folders.schemas import CreateFolderSchema, FolderSchema
from src.folders.services import create_folder_in_db, delete_folder_in_db, \
    reorder_folders_after_deletion, get_all_folders, add_chat_to_folder, \
    delete_chat_from_folder, pin_chat_in_folder
    
router = APIRouter(prefix='/folders', tags=['folders'])

@router.get('/')
async def get_all_folders(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
):
    folders = [json.loads(FolderSchema.model_validate(folder).model_dump_json())
               for folder in await get_all_folders(db, current_user)]
    data = {
        'total': len(folders),
        'items': folders
    }
    return data

@router.get('/{folder_uuid}/')
async def get_chats_from_folder(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    folder_uuid: UUID
):
    chats = [json.loads(FolderSchema.model_validate(folder).model_dump_json())
               for folder in await get_all_folders(db, current_user)]
    data = {
        'total': len(chats),
        'items': chats
    }
    return data

# only for custom
@router.post('/')
async def create_folder(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    folder_info: CreateFolderSchema,
):
    folder = await create_folder_in_db(db, current_user, folder_info)
    return FolderSchema.model_validate(folder)

# only for custom
@router.delete('/{folder_uuid}/')
async def delete_folder(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    folder_uuid: UUID
):
    await delete_folder_in_db(db, folder_uuid)
    await reorder_folders_after_deletion(db, current_user)
    return {'success': True}

@router.put('/add_chat')
async def add_chat(
    db: Annotated[AsyncSession, Depends(get_db)],
    chat_uuid: UUID,
    folder_uuid: UUID
):
    chat = await add_chat_to_folder(db, folder_uuid, chat_uuid)
    return ChatSchema.model_validate(chat)

@router.put('/delete_chat')
async def delete_chat(
    db: Annotated[AsyncSession, Depends(get_db)],
    chat_uuid: UUID,
    folder_uuid: UUID
):
    await delete_chat_from_folder(db, folder_uuid, chat_uuid)
    return {'success': True}

# toggles the 'is_pinned' field
@router.put('{chat_uuid}/pin')
async def pin_chat(
    db: Annotated[AsyncSession, Depends(get_db)],
    chat_uuid: UUID
):
    is_pinned = await pin_chat_in_folder(db, )
    return {'is_pinned': is_pinned}