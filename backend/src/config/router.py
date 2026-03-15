from typing import Annotated
import logging

from fastapi import APIRouter, Depends, File, UploadFile
from elasticsearch import AsyncElasticsearch
from sqlalchemy.ext.asyncio import AsyncSession

from src.settings import ELASTIC_USERS_INDEX_NAME
from src.database import get_db, get_es
from src.utils import validate_avatar
from src.dependencies import get_active_current_user
from src.auth.models import UserModel
from src.s3client import s3
from src.chats.services import get_chat_or_404
from src.config.schemas import UserConfigSchema, GroupConfigSchema
from src.config.services import update_user_config_in_db, update_user_config_in_elastic, \
    update_group_config_in_db, update_group_config_in_elastic
    
logger = logging.getLogger(__name__)

router = APIRouter(prefix='/config', tags=['config'])

@router.put('/user')
async def set_user_config(
    db: Annotated[AsyncSession, Depends(get_db)],
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    user_config: UserConfigSchema
):
    old_username = current_user.username

    await update_user_config_in_db(db, current_user, user_config)
    await update_user_config_in_elastic(es, user_config, old_username, current_user.uuid)

    logger.info(f"User {current_user.uuid} changed his settings")

    return {'success': True}

@router.put('/group')
async def set_group_config(
    db: Annotated[AsyncSession, Depends(get_db)],
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    group_config: GroupConfigSchema
):
    group = await get_chat_or_404(db, group_config.group_uuid)

    await update_group_config_in_db(db, group, current_user, group_config)
    await update_group_config_in_elastic(es, group_config)

    logger.info(f"Group settings {current_user.uuid} were changed by user {current_user.uuid}")

    return {'success': True}

@router.post('/avatar')
async def upload_avatar(
    db: Annotated[AsyncSession, Depends(get_db)],
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

    logger.info(f'New avatar {current_user.uuid} {url}')

    return {"avatar_url": url}