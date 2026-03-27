from typing import Annotated
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, File, UploadFile
from elasticsearch import AsyncElasticsearch
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.settings import ELASTIC_USERS_INDEX_NAME, ELASTIC_CHATS_INDEX_NAME,\
    REDIS_CHATS_KEY, REDIS_USERS_KEY
from src.database import get_db, get_es, get_redis
from src.utils import validate_avatar, invalidate_cache
from src.dependencies import get_active_current_user
from src.auth.models import UserModel
from src.s3client import s3
from src.chats.services import get_chat_or_404
from src.chats.utils import ensure_user_in_chat_or_403
from src.config.schemas import UserConfigSchema, GroupConfigSchema
from src.config.services import update_user_config_in_db, update_user_config_in_elastic, \
    update_group_config_in_db, update_group_config_in_elastic
    
logger = logging.getLogger(__name__)

router = APIRouter(prefix='/config', tags=['config'])

@router.put('/user')
async def set_user_config(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    user_config: UserConfigSchema
):
    old_username = current_user.username

    await update_user_config_in_db(db, current_user, user_config)
    await update_user_config_in_elastic(es, user_config, old_username, current_user.uuid)

    await invalidate_cache(r, REDIS_USERS_KEY, current_user.uuid)

    logger.info(f"User {current_user.uuid} changed his settings")

    return {'success': True}

@router.put('/group')
async def set_group_config(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    group_config: GroupConfigSchema
):
    group = await get_chat_or_404(db, group_config.uuid)

    await update_group_config_in_db(db, group, current_user, group_config)
    await update_group_config_in_elastic(es, group_config)

    await invalidate_cache(r, REDIS_CHATS_KEY, current_user.uuid)

    logger.info(f"Group settings {current_user.uuid} were changed by user {current_user.uuid}")

    return {'success': True}

@router.post('/user_avatar')
async def upload_user_avatar(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    file: UploadFile = File(...)
):
    object_name = validate_avatar(file)
    url = await s3.upload_file(file, object_name)

    current_user.avatar = url
    await db.commit()

    await es.update(
        index=ELASTIC_USERS_INDEX_NAME,
        id=str(current_user.uuid),
        doc={"avatar": url}
    )

    await invalidate_cache(r, REDIS_USERS_KEY, current_user.uuid)

    logger.info(f'New user avatar {current_user.uuid} {url}')

    return {"avatar_url": url}

@router.post('/group_avatar')
async def upload_group_avatar(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    group_uuid: UUID,
    file: UploadFile = File(...)
):
    group = await get_chat_or_404(db, group_uuid)
    ensure_user_in_chat_or_403(current_user, group)
    
    object_name = validate_avatar(file)
    url = await s3.upload_file(file, object_name)

    group.avatar = url
    await db.commit()

    await es.update(
        index=ELASTIC_CHATS_INDEX_NAME,
        id=str(group_uuid),
        doc={"avatar": url}
    )

    await invalidate_cache(r, REDIS_CHATS_KEY, current_user.uuid)

    logger.info(f'New group avatar {group_uuid} {url}')

    return {"avatar_url": url}