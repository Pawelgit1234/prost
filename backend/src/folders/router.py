from uuid import UUID
from typing import Annotated
import json

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from src.database import get_db, get_redis
from src.dependencies import get_active_current_user
from src.auth.models import UserModel
from src.folders.schemas import CreateFolderSchema, FolderSchema
from src.folders.services import create_folder_in_db, delete_folder_in_db, \
    reorder_folders_after_deletion, get_all_folders

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
async def get_chats_from_folder():
    pass

@router.post('/')
async def create_folder(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    folder_info: CreateFolderSchema,
):
    folder = await create_folder_in_db(db, current_user, folder_info)
    return FolderSchema.model_validate(folder)

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
async def add_chat():
    pass

@router.put('/remove_chat')
async def remove_chat():
    pass

@router.put('/move_folder')
async def move_folder():
    pass