import uuid

import pytest

from src.auth.services import create_user
from src.auth.schemas import UserRegisterSchema
from src.chats.schemas import CreateChatSchema
from src.chats.enums import ChatType
from src.chats.services import get_chat_list, create_chat_in_db, delete_chat_in_db, \
    quit_group_in_db, pin_chat_in_db, get_chat_or_404

@pytest.mark.asyncio
async def test_get_chat_list(get_db):
    user_data = UserRegisterSchema(
        first_name='John',
        last_name='Doe',
        username='johndoe',
        description='test user',
        email='john@example.com',
        password='Secret12%8800'
    )
    user = await create_user(get_db, user_data)

    chat_info = CreateChatSchema(
        chat_type=ChatType.GROUP,
        name='Test Group',
        group_description='Group description'
    )
    await create_chat_in_db(get_db, user, chat_info)

    chat_list = await get_chat_list(get_db, user)
    assert len(chat_list) == 1
    assert chat_list[0].name == 'Test Group'

@pytest.mark.asyncio
async def test_create_chat_in_db_with_chat(get_db):
    user1 = await create_user(get_db, UserRegisterSchema(
        first_name='User',
        last_name='One',
        username='user1',
        description='desc',
        email='user1@example.com',
        password='Secret12%8800'
    ))

    user2 = await create_user(get_db, UserRegisterSchema(
        first_name='User',
        last_name='Two',
        username='user2',
        description='desc',
        email='user2@example.com',
        password='Secret12%8800'
    ))

    chat_info = CreateChatSchema(
        chat_type=ChatType.NORMAL,
        name='user2',
    )
    chat = await create_chat_in_db(get_db, user1, chat_info)

    assert chat.chat_type == ChatType.NORMAL

@pytest.mark.asyncio
async def test_create_chat_in_db_with_group(get_db):
    user = await create_user(get_db, UserRegisterSchema(
        first_name='Group',
        last_name='Owner',
        username='groupowner',
        description='desc',
        email='groupowner@example.com',
        password='Secret12%8800'
    ))

    chat_info = CreateChatSchema(
        chat_type=ChatType.GROUP,
        name='Dev Group',
        group_description='Development group'
    )
    chat = await create_chat_in_db(get_db, user, chat_info)

    assert chat.chat_type == ChatType.GROUP
    assert chat.name == 'Dev Group'

@pytest.mark.asyncio
async def test_delete_chat_in_db(get_db):
    user = await create_user(get_db, UserRegisterSchema(
        first_name='Delete',
        last_name='Me',
        username='deleteme',
        description='desc',
        email='deleteme@example.com',
        password='Secret12%8800'
    ))

    chat_info = CreateChatSchema(
        chat_type=ChatType.GROUP,
        name='ToDelete',
        group_description='This will be deleted'
    )
    chat = await create_chat_in_db(get_db, user, chat_info)

    users = await delete_chat_in_db(get_db, chat.uuid)
    assert len(users) == 1
    assert users[0].username == user.username

@pytest.mark.asyncio
async def test_pin_chat_in_db(get_db):
    user = await create_user(get_db, UserRegisterSchema(
        first_name='Pin',
        last_name='User',
        username='pinuser',
        description='desc',
        email='pin@example.com',
        password='Secret12%8800'
    ))

    chat_info = CreateChatSchema(
        chat_type=ChatType.GROUP,
        name='PinChat',
        group_description='To pin'
    )
    chat = await create_chat_in_db(get_db, user, chat_info)

    is_pinned = await pin_chat_in_db(get_db, user, chat.uuid)
    assert is_pinned is True

    is_pinned_again = await pin_chat_in_db(get_db, user, chat.uuid)
    assert is_pinned_again is False