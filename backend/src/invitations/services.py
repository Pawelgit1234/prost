from datetime import datetime, timezone
import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select
from redis.asyncio import Redis
from elasticsearch import AsyncElasticsearch

from src.utils import save_to_db, get_object_or_404, get_all_objects
from src.auth.models import UserModel
from src.chats.models import ChatModel, UserChatAssociationModel
from src.chats.schemas import CreateChatSchema
from src.chats.enums import ChatType
from src.chats.utils import ensure_user_in_chat_or_403
from src.chats.services import create_chat_in_db, add_user_to_group_in_db
from src.invitations.models import InvitationModel
from src.invitations.enums import InvitationType
from src.invitations.schemas import InvitationSchema
from src.invitations.utils import convert_invitation_type_to_datetime

logger = logging.getLogger(__name__)

async def get_all_group_invitations_list(
    db: AsyncSession,
    user: UserModel,
    group: ChatModel
) -> list[InvitationModel]:
    ensure_user_in_chat_or_403(user, group, 'Only group members can see invitations')

    invitations = await get_all_objects(
        db, InvitationModel, InvitationModel.group_id == group.id,
    )

    return invitations

async def create_invitation_in_db(
    db: AsyncSession,
    user: UserModel,
    invitation_info: InvitationSchema
) -> InvitationModel:
    if invitation_info.invitation_type == InvitationType.USER:
        invitation = InvitationModel(
            invitation_type=invitation_info.invitation_type,
            max_uses=invitation_info.max_uses,
            lifetime=invitation_info.lifetime,
            user=user
        )
    elif invitation_info.invitation_type == InvitationType.GROUP:
        group = await get_object_or_404(
            db, ChatModel, ChatModel.uuid == invitation_info.group_uuid,
            detail='Group not found',
            options=[selectinload(ChatModel.user_associations)]
        )

        ensure_user_in_chat_or_403(user, group, 'Only group members can create an invitation')
        
        invitation = InvitationModel(
            invitation_type=invitation_info.invitation_type,
            max_uses=invitation_info.max_uses,
            lifetime=invitation_info.lifetime,
            group=group
        )

        logger.info(f'Invitation created in group {group.name} by {user.username}')
    
    return (await save_to_db(db, [invitation]))[0]

async def delete_invitation_in_db(
    db: AsyncSession,
    user: UserModel,
    invitation: InvitationModel
) -> None:
    if invitation.invitation_type == InvitationType.USER:
        if invitation.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You are not authorized to delete this invitation'
            )
    elif invitation.invitation_type == InvitationType.GROUP:
        ensure_user_in_chat_or_403(user, invitation.group, 'Only group members can delete invitations')

    await db.delete(invitation)
    await db.commit()

async def use_invitation(
    db: AsyncSession,
    r: Redis,
    es: AsyncElasticsearch,
    user: UserModel,
    invitation: InvitationModel
) -> None:
    lifetime = convert_invitation_type_to_datetime(invitation.lifetime)
    if lifetime is not None:
        if invitation.created_at + lifetime < datetime.now(timezone.utc):
            await db.delete(invitation)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Invitation to old'
            )
    
    if invitation.max_uses is not None:
        if invitation.max_uses == 1:
            await db.delete(invitation)
            logger.info("Invitation deleted after using it last time")
        else:
            invitation.max_uses -= 1

    # build in commit
    if invitation.invitation_type == InvitationType.USER:
        await db.refresh(user, ['chat_associations']) # loads chat_assoc
        await create_chat_in_db(db, r, user, CreateChatSchema(
            chat_type=ChatType.NORMAL,
            name=invitation.user.username
        ))
    elif invitation.invitation_type == InvitationType.GROUP:
        result = await db.execute(
            select(ChatModel)
            .options(selectinload(ChatModel.user_associations)
                    .selectinload(UserChatAssociationModel.user))
            .where(ChatModel.uuid == invitation.group.uuid)
        )
        group = result.scalar_one_or_none()
        await add_user_to_group_in_db(db, r, es, group, user)
