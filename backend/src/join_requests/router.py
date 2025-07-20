import json
import logging
from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db, get_redis
from src.dependencies import get_active_current_user
from src.utils import get_all_objects, get_object_or_404, wrap_list_response, serialize_model_list
from src.auth.models import UserModel
from src.chats.models import ChatModel
from src.join_requests.models import JoinRequestModel
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
    join_request_models = await get_all_objects(
        db, JoinRequestModel, JoinRequestModel.receiver_user_id == current_user.id
    )

    join_requests = serialize_model_list(join_request_models, JoinRequestSchema)
    return wrap_list_response(join_requests)

@router.get('/group')
async def get_all_group_join_requests(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    group_uuid: UUID
):
    group = await get_object_or_404(
        db, ChatModel, ChatModel.uuid == group_uuid, detail='Group not found',
        options=[selectinload(ChatModel.user_associations)]
    )
    join_requests_models = await get_all_group_join_requests_list(db, current_user, group)

    join_requests = [json.loads(JoinRequestSchema.model_validate(join_req).model_dump_json())
               for join_req in await join_requests_models]
    data = {
        'total': len(join_requests),
        'items': join_requests
    }

    return data

@router.post('/')
async def create_join_request(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    join_request_info: CreateJoinRequestSchema
):
    join_request = await create_join_request_in_db(db, current_user, join_request_info)
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
    await approve_join_request_in_db(db, r, current_user, join_request)
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
    await reject_join_request_in_db(db, current_user, join_request)
    return {'success': True}
