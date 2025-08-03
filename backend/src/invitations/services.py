from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import delete
from redis.asyncio import Redis
from elasticsearch import AsyncElasticsearch

from src.utils import save_to_db, get_object_or_404, get_all_objects
from src.auth.models import UserModel
from src.chats.models import ChatModel
from src.chats.schemas import CreateChatSchema
from src.chats.enums import ChatType
from src.chats.utils import is_user_in_chat
from src.chats.services import create_chat_in_db, add_user_to_group_in_db
from src.invitations.models import InvitationModel
from src.invitations.enums import InvitationType
from src.invitations.schemas import InvitationSchema
from src.invitations.utils import convert_invitation_type_to_datetime

async def get_all_group_invitations_list(
    db: AsyncSession,
    user: UserModel,
    group: ChatModel
) -> list[InvitationModel]:
    if not is_user_in_chat(user, group):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Only group members can get invitations'
        )

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
        
        if not is_user_in_chat(user, group):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You need to be in the Group to create an invitation'
            )

        invitation = InvitationModel(
            invitation_type=invitation_info.invitation_type,
            max_uses=invitation_info.max_uses,
            lifetime=invitation_info.lifetime,
            group=group
        )
    
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
        if not is_user_in_chat(user, invitation.group):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Only group members can delete invitations'
            )

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
    if invitation.created_at + lifetime > datetime.now():
        await db.delete(invitation)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Invitation not found'
        )
    
    if invitation.max_uses == 1:
        await db.delete(invitation)
    else:
        invitation.max_uses -= 1

    # build in commit
    if invitation.invitation_type == InvitationType.USER:
        await create_chat_in_db(db, r, user, CreateChatSchema(
            chat_type=ChatType.NORMAL,
            name=invitation.user.username
        ))
    elif invitation.invitation_type == InvitationType.GROUP:
        await add_user_to_group_in_db(db, r, es, invitation.group, user, invitation.user)
    
