from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

from src.auth.services import create_user
from src.auth.schemas import UserRegisterSchema
from src.chats.schemas import CreateChatSchema
from src.chats.enums import ChatType
from src.chats.models import ChatModel
from src.chats.services import create_chat_in_db, delete_chat_in_db

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

    mock_redis = AsyncMock()
    chat = await create_chat_in_db(get_db, mock_redis, user1, chat_info)

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

    mock_redis = AsyncMock()
    chat = await create_chat_in_db(get_db, mock_redis, user, chat_info)

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

    mock_redis = AsyncMock()
    chat = await create_chat_in_db(get_db, mock_redis, user, chat_info)
    await delete_chat_in_db(get_db, mock_redis, user, chat)

    # checks if the chat exists
    result = await get_db.execute(select(ChatModel).where(ChatModel.id == chat.id))
    assert result.scalar_one_or_none() is None