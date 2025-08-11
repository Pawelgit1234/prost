import json
import logging
from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from elasticsearch import AsyncElasticsearch

from src.settings import REDIS_USER_JOIN_REQUESTS_KEY, REDIS_GROUP_JOIN_REQUESTS_KEY, REDIS_CACHE_EXPIRE_SECONDS
from src.database import get_db, get_redis, get_es
from src.dependencies import get_active_current_user
from src.utils import get_all_objects, get_object_or_404, wrap_list_response, \
    invalidate_cache
from src.auth.models import UserModel
from src.chats.models import ChatModel
from src.join_requests.models import JoinRequestModel
from src.join_requests.enums import JoinRequestType
from src.join_requests.utils import serialize_join_request_model_list, get_join_request_or_404
from src.join_requests.schemas import CreateJoinRequestSchema, JoinRequestSchema
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
    redis_key = REDIS_USER_JOIN_REQUESTS_KEY.format(current_user.uuid)
    if data := await r.get(redis_key):
        return json.loads(data)

    join_request_models = await get_all_objects(
        db, JoinRequestModel, JoinRequestModel.receiver_user_id == current_user.id,
        options=[selectinload(JoinRequestModel.sender_user), selectinload(JoinRequestModel.receiver_user)]
    )
    join_requests = serialize_join_request_model_list(join_request_models)
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
    redis_key = REDIS_GROUP_JOIN_REQUESTS_KEY.format(group_uuid)
    if data := await r.get(redis_key):
        return json.loads(data)

    group = await get_object_or_404(
        db, ChatModel, ChatModel.uuid == group_uuid, detail='Group not found',
        options=[selectinload(ChatModel.user_associations)]
    )
    join_request_models = await get_all_group_join_requests_list(db, current_user, group)
    join_requests = serialize_join_request_model_list(join_request_models)
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
    
    if join_request_info.join_request_type == JoinRequestType.USER:
        await invalidate_cache(r, REDIS_USER_JOIN_REQUESTS_KEY, join_request_info.target_uuid)
    elif join_request_info.join_request_type == JoinRequestType.GROUP:
        await invalidate_cache(r, REDIS_GROUP_JOIN_REQUESTS_KEY, join_request_info.target_uuid)
    
    logger.info(f'Join request created by {current_user.username}')
    return JoinRequestSchema(
        uuid=join_request.uuid,
        join_request_type=join_request_info.join_request_type,
        target_uuid=join_request_info.target_uuid,
        sender_user_uuid=current_user.uuid
    )


@router.delete('/approve')
async def approve_join_request(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    join_request_uuid: UUID,
):
    join_request = await get_join_request_or_404(db, join_request_uuid)
    sender_username = join_request.sender_user.username
    
    await approve_join_request_in_db(db, r, es, current_user, join_request)

    if join_request.join_request_type == JoinRequestType.USER:
        await invalidate_cache(r, REDIS_USER_JOIN_REQUESTS_KEY, current_user.uuid)
    elif join_request.join_request_type == JoinRequestType.GROUP:
        await invalidate_cache(r, REDIS_GROUP_JOIN_REQUESTS_KEY, join_request.group.uuid)

    logger.info(f'Join request from {sender_username} approved by {current_user.username}')
    return {'success': True}

@router.delete('/reject')
async def reject_join_request(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    join_request_uuid: UUID,
):
    join_request = await get_join_request_or_404(db, join_request_uuid)
    sender_username = join_request.sender_user.username

    await reject_join_request_in_db(db, current_user, join_request)
    
    if join_request.join_request_type == JoinRequestType.USER:
        await invalidate_cache(r, REDIS_USER_JOIN_REQUESTS_KEY, current_user.uuid)
    elif join_request.join_request_type == JoinRequestType.GROUP:
        await invalidate_cache(r, REDIS_GROUP_JOIN_REQUESTS_KEY, join_request.group.uuid)

    logger.info(f'Join request from {sender_username} rejected by {current_user.username}')
    return {'success': True}
