import uuid

import pytest
from fastapi import HTTPException

from src.auth.schemas import UserRegisterSchema
from src.auth.services import create_user, authenticate_user, create_email_activation_token, \
    activate_user

@pytest.mark.asyncio
async def test_valid_user_auth(get_db):
    user_data = UserRegisterSchema(
        first_name='John',
        last_name='Doe',
        username='johndoe',
        description='test user',
        email='john@example.com',
        password='Secret12%8800'
    )

    user = await create_user(get_db, user_data)
    result = await authenticate_user(get_db, user_data.username, user_data.password)

    assert result
    assert user.username == result.username

@pytest.mark.asyncio
async def test_invalid_user_auth(get_db):
    user_data = UserRegisterSchema(
        first_name='John',
        last_name='Doe',
        username='johndoe',
        description='test user',
        email='john@example.com',
        password='Secret12%8800'
    )

    result = await authenticate_user(get_db, 'Barbara', 'other_secret')
    assert not result

@pytest.mark.asyncio
async def test_valid_user_activation(get_db):
    user_data = UserRegisterSchema(
        first_name='John',
        last_name='Doe',
        username='johndoe',
        description='test user',
        email='john@example.com',
        password='Secret12%8800'
    )

    user = await create_user(get_db, user_data)
    token = await create_email_activation_token(get_db, user)
    activated_user = await activate_user(get_db, token.uuid, user)

    assert activated_user.is_active

@pytest.mark.asyncio
async def test_invalid_user_activation(get_db):
    user_data = UserRegisterSchema(
        first_name='John',
        last_name='Doe',
        username='johndoe',
        description='test user',
        email='john@example.com',
        password='Secret12%8800'
    )

    user = await create_user(get_db, user_data)

    with pytest.raises(HTTPException) as exc_info:
        await activate_user(get_db, uuid.uuid4(), user)

    assert exc_info.value.status_code == 404
    assert 'Invalid or expired activation Token' in exc_info.value.detail
