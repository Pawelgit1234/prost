import json
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from elasticsearch import AsyncElasticsearch

from src.settings import HOST, REDIS_CACHE_EXPIRE_SECONDS, REDIS_USER_INVITATION_KEY,\
    REDIS_GROUP_INVITATION_KEY
from src.database import get_db, get_redis, get_es
from src.dependencies import get_active_current_user
from src.utils import get_all_objects, get_object_or_404, wrap_list_response, \
    invalidate_cache, serialize_model_list
from src.auth.models import UserModel
from src.chats.models import ChatModel
from src.invitations.models import InvitationModel
from src.invitations.enums import InvitationType
from src.invitations.utils import get_invitation_or_404
from src.invitations.services import create_invitation_in_db, get_all_group_invitations_list, \
    delete_invitation_in_db, use_invitation
from src.invitations.schemas import InvitationSchema, CreateInvitationSchema

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/invitations', tags=['invitations'])

@router.get('/user')
async def get_all_user_invitations(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
):
    redis_key = REDIS_USER_INVITATION_KEY.format(current_user.uuid)
    if data := await r.get(redis_key):
        return json.loads(data)

    invitation_models = await get_all_objects(
        db, InvitationModel, InvitationModel.user_id == current_user.id,
    )
    invitations = serialize_model_list(invitation_models, InvitationSchema)
    data = wrap_list_response(invitations)

    await r.set(
        redis_key,
        json.dumps(data),
        REDIS_CACHE_EXPIRE_SECONDS
    )
    return data

@router.get('/group')
async def get_all_group_invitations(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    group_uuid: UUID
):
    redis_key = REDIS_GROUP_INVITATION_KEY.format(group_uuid)
    if data := await r.get(redis_key):
        return json.loads(data)

    group = await get_object_or_404(
        db, ChatModel, ChatModel.uuid == group_uuid, detail='Group not found',
        options=[selectinload(ChatModel.user_associations)]
    )
    invitation_models = await get_all_group_invitations_list(db, current_user, group)
    invitations = serialize_model_list(invitation_models, InvitationSchema)
    data = wrap_list_response(invitations)

    await r.set(
        redis_key,
        json.dumps(data),
        REDIS_CACHE_EXPIRE_SECONDS
    )
    return data

@router.post('/')
async def create_invitation(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    invitation_info: CreateInvitationSchema,
):
    invitation = await create_invitation_in_db(db, current_user, invitation_info)

    if invitation.invitation_type == InvitationType.USER:
        await invalidate_cache(r, REDIS_USER_INVITATION_KEY, current_user.uuid)
        logger.info(f'Invitation created by {current_user.username}')
    elif invitation.invitation_type == InvitationType.GROUP:
        await invalidate_cache(r, REDIS_GROUP_INVITATION_KEY, invitation_info.group_uuid)
    
    return InvitationSchema.model_validate(invitation)

@router.delete('/')
async def delete_invitation(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    invitation_uuid: UUID
):
    invitation = await get_invitation_or_404(db, invitation_uuid)
    await delete_invitation_in_db(db, current_user, invitation)

    if invitation.invitation_type == InvitationType.USER:
        await invalidate_cache(r, REDIS_USER_INVITATION_KEY, current_user.uuid)
        logger.info(f'Invitation deleted by {current_user.username}')
    elif invitation.invitation_type == InvitationType.GROUP:
        await invalidate_cache(r, REDIS_GROUP_INVITATION_KEY, invitation.group.uuid)
        logger.info(f'Invitation deleted from group {invitation.group.name} by {current_user.username}')

    return {'success': True}

@router.get('/join/')
async def join_via_invitation(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    invitation_uuid: UUID
):
    invitation = await get_invitation_or_404(db, invitation_uuid)
    await use_invitation(db, r, es, current_user, invitation)

    if invitation.invitation_type == InvitationType.USER:
        await invalidate_cache(r, REDIS_USER_INVITATION_KEY, current_user.uuid)
        logger.info(f'{current_user.username} created a chat via invitation with {invitation.user.username}')
    elif invitation.invitation_type == InvitationType.GROUP:
        await invalidate_cache(r, REDIS_GROUP_INVITATION_KEY, invitation.group.uuid)
        logger.info(f"{current_user.username} joined a group '{invitation.group.name}' via invitation")

    return {'success': True}