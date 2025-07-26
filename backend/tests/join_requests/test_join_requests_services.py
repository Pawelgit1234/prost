from unittest.mock import AsyncMock

import pytest
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from src.utils import get_object_or_404
from src.auth.models import UserModel
from src.auth.schemas import UserRegisterSchema
from src.auth.services import create_user
from src.chats.services import create_chat_in_db
from src.chats.schemas import CreateChatSchema
from src.chats.utils import get_common_chats
from src.chats.enums import ChatType
from src.join_requests.models import JoinRequestModel
from src.join_requests.services import create_join_request_in_db, \
    approve_join_request_in_db, reject_join_request_in_db
from src.join_requests.schemas import CreateJoinRequestSchema
from src.join_requests.enums import JoinRequestType

@pytest.mark.asyncio
async def test_create_join_request_in_db_with_user(get_db):
    sender_user = await create_user(get_db, UserRegisterSchema(
        first_name='John',
        last_name='Doe',
        username='johndoe',
        description='test user',
        email='john@example.com',
        password='Secret12%8800'
    ))
    receiver_user = await create_user(get_db, UserRegisterSchema(
        first_name='John2',
        last_name='Doe2',
        username='johndoe2',
        description='test user2',
        email='john2@example.com',
        password='Lobaboba%8800'
    ))

    join_request = await create_join_request_in_db(get_db, sender_user, CreateJoinRequestSchema(
        target_uuid=receiver_user.uuid, join_request_type=JoinRequestType.USER
    ))

    assert join_request.receiver_user_id == receiver_user.id
    assert join_request.sender_user_id == sender_user.id

@pytest.mark.asyncio
async def test_create_join_request_in_db_with_group(get_db):
    sender_user = await create_user(get_db, UserRegisterSchema(
        first_name='John',
        last_name='Doe',
        username='johndoe',
        description='test user',
        email='john@example.com',
        password='Secret12%8800'
    ))
    group_user = await create_user(get_db, UserRegisterSchema(
        first_name='John2',
        last_name='Doe2',
        username='johndoe2',
        description='test user2',
        email='john2@example.com',
        password='Lobaboba%8800'
    ))

    mock_redis = AsyncMock()
    group = await create_chat_in_db(get_db, mock_redis, group_user, CreateChatSchema(
        chat_type=ChatType.GROUP, name='Group'
    ))

    join_request = await create_join_request_in_db(get_db, sender_user, CreateJoinRequestSchema(
        target_uuid=group.uuid, join_request_type=JoinRequestType.GROUP
    ))

    assert join_request.group_id == group.id
    assert join_request.sender_user_id == sender_user.id

@pytest.mark.asyncio
async def test_approve_join_request_in_db_with_user(get_db):
    sender_user = await create_user(get_db, UserRegisterSchema(
        first_name='John',
        last_name='Doe',
        username='johndoe',
        description='test user',
        email='john@example.com',
        password='Secret12%8800'
    ))
    receiver_user = await create_user(get_db, UserRegisterSchema(
        first_name='John2',
        last_name='Doe2',
        username='johndoe2',
        description='test user2',
        email='john2@example.com',
        password='Lobaboba%8800'
    ))

    join_request = await create_join_request_in_db(get_db, sender_user, CreateJoinRequestSchema(
        target_uuid=receiver_user.uuid, join_request_type=JoinRequestType.USER
    ))

    mock_redis = AsyncMock()
    mock_es = AsyncMock()
    await approve_join_request_in_db(get_db, mock_redis, mock_es, receiver_user, join_request)

    with pytest.raises(HTTPException) as exc_info:
        await get_object_or_404(get_db, JoinRequestModel, JoinRequestModel.id == join_request.id)
    
    common_chats = await get_common_chats(get_db, sender_user, receiver_user)
    chat_types = [chat.chat_type for chat in common_chats]
    
    assert ChatType.NORMAL in chat_types
    assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test_approve_join_request_in_db_with_group(get_db):
    sender_user = await create_user(get_db, UserRegisterSchema(
        first_name='John',
        last_name='Doe',
        username='johndoe',
        description='test user',
        email='john@example.com',
        password='Secret12%8800'
    ))
    group_user = await create_user(get_db, UserRegisterSchema(
        first_name='John2',
        last_name='Doe2',
        username='johndoe2',
        description='test user2',
        email='john2@example.com',
        password='Lobaboba%8800'
    ))
    # workaround
    sender_user = await get_object_or_404(
        get_db, UserModel, UserModel.id == sender_user.id, options=[selectinload(UserModel.chat_associations)]
    )
    group_user = await get_object_or_404(
        get_db, UserModel, UserModel.id == group_user.id, options=[selectinload(UserModel.chat_associations)]
    )

    mock_redis = AsyncMock()
    group = await create_chat_in_db(get_db, mock_redis, group_user, CreateChatSchema(
        chat_type=ChatType.GROUP, name='Group'
    ))

    join_request = await create_join_request_in_db(get_db, sender_user, CreateJoinRequestSchema(
        target_uuid=group.uuid, join_request_type=JoinRequestType.GROUP
    ))

    mock_redis = AsyncMock()
    mock_es = AsyncMock()
    await approve_join_request_in_db(get_db, mock_redis, mock_es, group_user, join_request)

    with pytest.raises(HTTPException) as exc_info:
        await get_object_or_404(get_db, JoinRequestModel, JoinRequestModel.id == join_request.id)
    
    common_chats = await get_common_chats(get_db, sender_user, group_user)
    chat_uuids = [chat.uuid for chat in common_chats]
    
    assert group.uuid in chat_uuids
    assert exc_info.value.status_code == 404
   
@pytest.mark.asyncio
async def test_reject_join_request_in_db(get_db):
    sender_user = await create_user(get_db, UserRegisterSchema(
        first_name='John',
        last_name='Doe',
        username='johndoe',
        description='test user',
        email='john@example.com',
        password='Secret12%8800'
    ))
    receiver_user = await create_user(get_db, UserRegisterSchema(
        first_name='John2',
        last_name='Doe2',
        username='johndoe2',
        description='test user2',
        email='john2@example.com',
        password='Lobaboba%8800'
    ))

    join_request = await create_join_request_in_db(get_db, sender_user, CreateJoinRequestSchema(
        target_uuid=receiver_user.uuid, join_request_type=JoinRequestType.USER
    ))

    await reject_join_request_in_db(get_db, receiver_user, join_request)

    with pytest.raises(HTTPException) as exc_info:
        await get_object_or_404(get_db, JoinRequestModel, JoinRequestModel.id == join_request.id)
    
    assert exc_info.value.status_code == 404

