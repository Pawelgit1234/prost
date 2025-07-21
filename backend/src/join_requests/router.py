import json
import logging
from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.settings import REDIS_USER_JOIN_REQUESTS_KEY, REDIS_GROUP_JOIN_REQUESTS_KEY, REDIS_CACHE_EXPIRE_SECONDS
from src.database import get_db, get_redis
from src.dependencies import get_active_current_user
from src.utils import get_all_objects, get_object_or_404, wrap_list_response, serialize_model_list
from src.auth.models import UserModel
from src.chats.models import ChatModel
from src.join_requests.models import JoinRequestModel
from src.join_requests.schemas import CreateJoinRequestSchema, JoinRequestSchema
from src.join_requests.utils import invalidate_cache_specific
from src.join_requests.services import create_join_request_in_db, get_all_group_join_requests_list, \
    approve_join_request_in_db, reject_join_request_in_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/join_requests', tags=['join_requests'])

@router.get('/user')
async def get_all_user_join_requests(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
):
    redis_key = REDIS_USER_JOIN_REQUESTS_KEY.format(str(current_user.uuid))
    if data := await r.get(redis_key):
        return json.loads(data)

    join_request_models = await get_all_objects(
        db, JoinRequestModel, JoinRequestModel.receiver_user_id == current_user.id
    )
    join_requests = serialize_model_list(join_request_models, JoinRequestSchema)
    data = wrap_list_response(join_requests)

    await r.set(
        redis_key,
        json.dumps(data),
        REDIS_CACHE_EXPIRE_SECONDS
    )
    return data

@router.get('/group')
async def get_all_group_join_requests(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    group_uuid: UUID
):
    redis_key = REDIS_GROUP_JOIN_REQUESTS_KEY.format(str(group_uuid))
    if data := await r.get(redis_key):
        return json.loads(data)

    group = await get_object_or_404(
        db, ChatModel, ChatModel.uuid == group_uuid, detail='Group not found',
        options=[selectinload(ChatModel.user_associations)]
    )
    join_request_models = await get_all_group_join_requests_list(db, current_user, group)
    join_requests = serialize_model_list(join_request_models, JoinRequestSchema)
    data = wrap_list_response(join_requests)

    await r.set(
        redis_key,
        json.dumps(data),
        REDIS_CACHE_EXPIRE_SECONDS
    )
    return data

@router.post('/')
async def create_join_request(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    join_request_info: CreateJoinRequestSchema
):
    join_request = await create_join_request_in_db(db, current_user, join_request_info)
    await invalidate_cache_specific(r, join_request)
    logger.info(f'Join request created by {current_user.username}')
    return JoinRequestSchema.model_validate(join_request)

@router.delete('/approve')
async def approve_join_request(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    join_request_uuid: UUID,
):
    join_request = await get_object_or_404(
        db, JoinRequestModel, JoinRequestModel.uuid == join_request_uuid,
        detail='Join request not found'
    )
    sender_username = join_request.user.username
    
    await approve_join_request_in_db(db, r, current_user, join_request)
    await invalidate_cache_specific(r, join_request)

    logger.info(f'Join request from {sender_username} approved by {current_user.username}')
    return {'success': True}

@router.delete('/reject')
async def reject_join_request(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    join_request_uuid: UUID,
):
    join_request = await get_object_or_404(
        db, JoinRequestModel, JoinRequestModel.uuid == join_request_uuid,
        detail='Join request not found'
    )
    sender_username = join_request.user.username

    await reject_join_request_in_db(db, current_user, join_request)
    await invalidate_cache_specific(r, join_request)

    logger.info(f'Join request from {sender_username} rejected by {current_user.username}')
    return {'success': True}
