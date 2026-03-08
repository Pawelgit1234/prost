from typing import Annotated
import logging

from fastapi import APIRouter, Depends, File, UploadFile
from elasticsearch import AsyncElasticsearch
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from src.database import get_db, get_redis, get_es
from src.utils import validate_avatar
from src.dependencies import get_active_current_user
from src.auth.models import UserModel
from src.s3client import s3
from src.config.schemas import UserConfigSchema, GroupConfigSchema
    
logger = logging.getLogger(__name__)

router = APIRouter(prefix='/config', tags=['config'])

@router.post('/user')
async def set_user_config(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    user_config: UserConfigSchema
):
    current_user.first_name = user_config.first_name
    current_user.last_name = user_config.last_name
    current_user.username = user_config.username
    current_user.description = user_config.description
    current_user.is_visible = user_config.is_visible
    current_user.is_open_for_messages = user_config.is_open_for_messages
    current_user.avatar = user_config.avatar_url
    await db.commit()

    return {'success': True}

@router.post('/group')
async def set_group_config(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    group_config: GroupConfigSchema
):
    return {'success': True}

@router.post('/avatar')
async def upload_avatar(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    file: UploadFile = File(...)
):
    object_name = validate_avatar(file)
    url = await s3.upload_file(file, object_name)

    # TODO: elastic and redis
    current_user.avatar = url
    await db.commit()

    logger.info(f'New avatar {current_user.uuid} {url}')

    return {"avatar_url": url}