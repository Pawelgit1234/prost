from unittest.mock import AsyncMock

import pytest
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from tests.utils import create_user1, create_user2
from src.utils import get_object_or_404
from src.auth.models import UserModel
from src.auth.schemas import UserRegisterSchema
from src.chats.services import create_chat_in_db
from src.chats.schemas import CreateChatSchema
from src.chats.utils import get_common_chats
from src.chats.enums import ChatType
from src.invitations.enums import InvitationType, InvitationLifetime
from src.invitations.models import InvitationModel
from src.invitations.schemas import CreateInvitationSchema
from src.invitations.services import create_invitation_in_db, delete_invitation_in_db, use_invitation
from src.chats.services import create_chat_in_db, add_user_to_group_in_db

@pytest.mark.asyncio
async def test_create_invitation_in_db_with_user(get_db):
    user = await create_user1(get_db)
    invitation = await create_invitation_in_db(
        get_db, user, CreateInvitationSchema(
            invitation_type=InvitationType.USER,
            lifetime=InvitationLifetime.UNLIMITED,
            max_uses=None
        )
    )

    assert invitation.user_id == user.id

@pytest.mark.asyncio
async def test_create_invitation_in_db_with_group(get_db):
    user = await create_user1(get_db)

    mock_redis = AsyncMock()
    group = await create_chat_in_db(get_db, mock_redis, user, CreateChatSchema(
        chat_type=ChatType.GROUP, name='Group'
    ))

    invitation = await create_invitation_in_db(
        get_db, user, CreateInvitationSchema(
            invitation_type=InvitationType.GROUP,
            lifetime=InvitationLifetime.UNLIMITED,
            max_uses=None,
            group_uuid=group.uuid
        )
    )

    assert invitation.group_id == group.id

@pytest.mark.asyncio
async def test_delete_invitation_in_db_with_user(get_db):
    user = await create_user1(get_db)
    invitation = await create_invitation_in_db(
        get_db, user, CreateInvitationSchema(
            invitation_type=InvitationType.USER,
            lifetime=InvitationLifetime.UNLIMITED,
            max_uses=None
        )
    )

    await delete_invitation_in_db(get_db, user, invitation)
    with pytest.raises(HTTPException) as exc_info:
        await get_object_or_404(get_db, InvitationModel, InvitationModel.id == invitation.id)
    assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test_delete_invitation_in_db_with_group(get_db):
    user = await create_user1(get_db)

    mock_redis = AsyncMock()
    group = await create_chat_in_db(get_db, mock_redis, user, CreateChatSchema(
        chat_type=ChatType.GROUP, name='Group'
    ))

    invitation = await create_invitation_in_db(
        get_db, user, CreateInvitationSchema(
            invitation_type=InvitationType.GROUP,
            lifetime=InvitationLifetime.UNLIMITED,
            max_uses=None,
            group_uuid=group.uuid
        )
    )
    
    await delete_invitation_in_db(get_db, user, invitation)
    with pytest.raises(HTTPException) as exc_info:
        await get_object_or_404(get_db, InvitationModel, InvitationModel.id == invitation.id)
    assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test_use_invitation_in_db_with_user(get_db):
    user1 = await create_user1(get_db)
    invitation = await create_invitation_in_db(
        get_db, user1, CreateInvitationSchema(
            invitation_type=InvitationType.USER,
            lifetime=InvitationLifetime.UNLIMITED,
            max_uses=None
        )
    )

    user2 = await create_user2(get_db)
    mock_redis = AsyncMock()
    mock_es = AsyncMock()
    await use_invitation(get_db, mock_redis, mock_es, user2, invitation)

    common_chats = await get_common_chats(get_db, user1, user2)
    chat_types = [chat.chat_type for chat in common_chats]
    assert ChatType.NORMAL in chat_types

@pytest.mark.asyncio
async def test_use_invitation_in_db_with_group(get_db):
    user1 = await create_user1(get_db)
    await get_db.refresh(user1, ['chat_associations']) # loads chat_assoc

    mock_redis = AsyncMock()
    group = await create_chat_in_db(get_db, mock_redis, user1, CreateChatSchema(
        chat_type=ChatType.GROUP, name='Group'
    ))

    invitation = await create_invitation_in_db(
        get_db, user1, CreateInvitationSchema(
            invitation_type=InvitationType.GROUP,
            lifetime=InvitationLifetime.UNLIMITED,
            max_uses=None,
            group_uuid=group.uuid
        )
    )

    user2 = await create_user2(get_db)
    await get_db.refresh(user2, ['chat_associations']) # loads chat_assoc

    mock_redis = AsyncMock()
    mock_es = AsyncMock()
    await use_invitation(get_db, mock_redis, mock_es, user2, invitation)

    common_chats = await get_common_chats(get_db, user1, user2)
    chat_uuids = [chat.uuid for chat in common_chats]
    assert group.uuid in chat_uuids