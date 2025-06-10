import asyncio
import json
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.utils import invalidate_cache
from src.chats.services import create_chat_in_db, delete_chat_in_db,\
    quit_group_in_db, add_user_to_group_in_db
from src.chats.schemas import CreateChatSchema, ChatSchema
from src.dependencies import get_active_current_user
from src.auth.models import UserModel
from src.database import get_db, get_redis
from src.settings import REDIS_CHATS_KEY

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/chats', tags=['chats'])

@router.post('/')
async def create_chat(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    chat_info: CreateChatSchema
):
    chat = await create_chat_in_db(db, current_user, chat_info)
    await invalidate_cache(r, REDIS_CHATS_KEY, current_user.uuid)
    return ChatSchema.model_validate(chat)

@router.delete('/{chat_uuid}')
async def delete_chat(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    chat_uuid: UUID
):
    users = await delete_chat_in_db(db, current_user, chat_uuid)

    # is faster
    tasks = [invalidate_cache(r, REDIS_CHATS_KEY, user.uuid) for user in users]
    await asyncio.gather(*tasks)

    return {'success': True}

# you can quit a group without deleting it
@router.delete('/{group_uuid}/quit')
async def quit_group(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    group_uuid: UUID
):
    await quit_group_in_db(db, current_user, group_uuid)
    await invalidate_cache(r, REDIS_CHATS_KEY, current_user.uuid)
    return {'success': True}

@router.post('{group_uuid}/add_user')
async def add_user_to_group(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    group_uuid: UUID,
    username: str
):
    added_user = await add_user_to_group_in_db(db, group_uuid, username, current_user)
    await invalidate_cache(r, REDIS_CHATS_KEY, added_user.uuid)
    return {'success': True}