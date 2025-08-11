import asyncio
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from elasticsearch import AsyncElasticsearch

from src.chats.services import create_chat_in_db, delete_chat_in_db,\
    quit_group_in_db, user_add_user_to_group_in_db, get_chat_or_404
from src.chats.utils import get_group_users_uuids
from src.chats.schemas import CreateChatSchema, ChatSchema
from src.dependencies import get_active_current_user
from src.utils import get_object_or_404
from src.settings import ELASTIC_CHATS_INDEX_NAME
from src.auth.models import UserModel
from src.database import get_db, get_redis, get_es

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/chats', tags=['chats'])

@router.post('/')
async def create_chat(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    chat_info: CreateChatSchema
):
    chat = await create_chat_in_db(db, r, current_user, chat_info)
    await es.index(
        index=ELASTIC_CHATS_INDEX_NAME,
        id=str(chat.uuid),
        document={
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
    await delete_chat_in_db(db, r, current_user, chat)
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
    await quit_group_in_db(db, r, es, current_user, group)
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

    group = await user_add_user_to_group_in_db(db, r, es, group, other_user, current_user)
    return {'success': True}
