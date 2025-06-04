from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from src.database import get_db, get_redis
from src.dependencies import get_active_current_user
from src.auth.models import UserModel
from src.folders.schemas import CreateFolderSchema
from src.folders.services import create_folder_in_db

router = APIRouter(prefix='/folders', tags=['folders'])

@router.get('/')
async def get_all_folders():
    pass

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
    pass

@router.delete('/{folder_uuid}/')
async def delete_folder(folder_uuid: UUID):
    pass

@router.put('/add_chat')
async def add_chat():
    pass

@router.put('/remove_chat')
async def remove_chat():
    pass

@router.put('/move_folder')
async def move_folder():
    pass