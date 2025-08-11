from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from fastapi import HTTPException

from tests.utils import create_user1
from src.folders.services import get_chats_list_from_folder, create_folder_in_db, \
    delete_folder_in_db, add_chat_to_folder, delete_chat_from_folder, pin_chat_in_folder, \
    get_folder_chat_assoc_or_404
from src.folders.schemas import CreateFolderSchema
from src.folders.models import FolderModel
from src.folders.enums import FolderType
from src.chats.services import create_chat_in_db
from src.chats.schemas import CreateChatSchema
from src.chats.enums import ChatType
from src.auth.schemas import UserRegisterSchema
from src.auth.services import create_user

@pytest.mark.asyncio
async def test_get_chats_list_from_folder(get_db):
    user = await create_user1(get_db)
    folder = await create_folder_in_db(get_db, user, CreateFolderSchema(name='folder'))

    chat_info = CreateChatSchema(
        chat_type=ChatType.GROUP,
        name='ToDelete',
        group_description='This will be deleted'
    )
    mock_redis = AsyncMock()
    chat = await create_chat_in_db(get_db, mock_redis, user, chat_info)
    await add_chat_to_folder(get_db, user, folder, chat)

    folders = await get_chats_list_from_folder(get_db, user, folder.uuid)
    assert len(folders) == 1
    
@pytest.mark.asyncio
async def test_create_folder_in_db(get_db):
    user = await create_user1(get_db)
    folder = await create_folder_in_db(get_db, user, CreateFolderSchema(name='folder'))

    assert folder.folder_type == FolderType.CUSTOM

@pytest.mark.asyncio
async def test_delete_folder_in_db(get_db):
    user = await create_user1(get_db)
    folder = await create_folder_in_db(get_db, user, CreateFolderSchema(name='folder'))
    await delete_folder_in_db(get_db, user, folder)
    
    # checks if the chat exists
    result = await get_db.execute(select(FolderModel).where(FolderModel.id == folder.id))
    assert result.scalar_one_or_none() is None

@pytest.mark.asyncio
async def test_add_chat_to_folder(get_db):
    user = await create_user1(get_db)
    folder = await create_folder_in_db(get_db, user, CreateFolderSchema(name='folder'))
    
    chat_info = CreateChatSchema(
        chat_type=ChatType.GROUP,
        name='ToDelete',
        group_description='This will be deleted'
    )
    mock_redis = AsyncMock()
    chat = await create_chat_in_db(get_db, mock_redis, user, chat_info)
    await add_chat_to_folder(get_db, user, folder, chat)

    # if 404 is not raised, then is it ok
    await get_folder_chat_assoc_or_404(get_db, user, folder.uuid, chat.uuid)

@pytest.mark.asyncio
async def test_delete_chat_from_folder(get_db):
    user = await create_user1(get_db)
    folder = await create_folder_in_db(get_db, user, CreateFolderSchema(name='folder'))
    
    chat_info = CreateChatSchema(
        chat_type=ChatType.GROUP,
        name='ToDelete',
        group_description='This will be deleted'
    )
    mock_redis = AsyncMock()
    chat = await create_chat_in_db(get_db, mock_redis, user, chat_info)

    await add_chat_to_folder(get_db, user, folder, chat)
    assoc = await get_folder_chat_assoc_or_404(get_db, user, folder.uuid, chat.uuid)
    await delete_chat_from_folder(get_db, assoc)

    with pytest.raises(HTTPException) as exc_info:
        await get_folder_chat_assoc_or_404(get_db, user, folder.uuid, chat.uuid)

    assert exc_info.value.status_code == 404

@pytest.mark.asyncio
async def test_pin_chat_in_folder(get_db):
    user = await create_user1(get_db)
    folder = await create_folder_in_db(get_db, user, CreateFolderSchema(name='folder'))

    chat_info = CreateChatSchema(
        chat_type=ChatType.GROUP,
        name='ToDelete',
        group_description='This will be deleted'
    )
    mock_redis = AsyncMock()
    chat = await create_chat_in_db(get_db, mock_redis, user, chat_info)
    await add_chat_to_folder(get_db, user, folder, chat)

    assoc = await get_folder_chat_assoc_or_404(get_db, user, folder.uuid, chat.uuid)
    
    # pinned
    is_pinned = await pin_chat_in_folder(get_db, assoc)
    assert is_pinned

    # unpinned
    is_pinned = await pin_chat_in_folder(get_db, assoc)
    assert not is_pinned
 