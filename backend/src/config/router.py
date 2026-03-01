from typing import Annotated
import logging

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from src.database import get_db, get_redis
from src.utils import validate_avatar
from src.dependencies import get_active_current_user
from src.auth.models import UserModel
from src.s3client import s3
    
logger = logging.getLogger(__name__)

router = APIRouter(prefix='/config', tags=['config'])

@router.get('/user')
async def get_user_config(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
):
    pass

# TODO: get group settings

# TODO: set group settings

# TODO: set group settings

@router.post('/avatar')
async def upload_avatar(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    file: UploadFile = File(...)
):
    object_name = validate_avatar(file)
    url = await s3.upload_file(file, object_name)

    current_user.avatar = url
    await db.commit()

    return {"avatar_url": url}