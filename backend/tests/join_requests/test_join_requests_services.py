from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from fastapi import HTTPException

from src.auth.models import UserModel
from src.auth.schemas import UserRegisterSchema
from src.auth.services import create_user
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
    pass

@pytest.mark.asyncio
async def test_approve_join_request_in_db_with_user(get_db):
    pass

@pytest.mark.asyncio
async def test_approve_join_request_in_db_with_group(get_db):
    pass

@pytest.mark.asyncio
async def test_reject_join_request_in_db(get_db):
    pass