import logging

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from elasticsearch import AsyncElasticsearch

from src.settings import REDIS_MESSAGES_KEY, REDIS_FOLDERS_KEY
from src.utils import invalidate_cache
from src.auth.models import UserModel
from src.chats.services import get_chat_or_none
from src.chats.utils import is_user_in_chat
from src.messages.connection_manager import ConnectionManager
from src.messages.schemas import ReceiveMessageSchema, SendMessageSchema, \
    ChatActionSchema, ChatActionSchema
from src.messages.services import create_message_in_db, add_chat_to_new_folder_for_all, \
    mark_chat_read, remove_chat_from_new_folder
from src.messages.utils import add_message_to_elastic, delete_cache_for_users

logger = logging.getLogger(__name__)
connection_manager = ConnectionManager()

@connection_manager.handler("new_message")
async def new_message_handler(
    db: AsyncSession,
    r: Redis,
    es: AsyncElasticsearch,
    ws: WebSocket,
    current_user: UserModel,
    incomming_message: dict,
    **kwargs,
):
    message_schema = ReceiveMessageSchema(**incomming_message)
    chat = await get_chat_or_none(db, message_schema.chat_uuid)
    if not chat:
        await connection_manager.send_error("Chat not found", ws)
        return
    
    message = await create_message_in_db(
        db, current_user, chat, message_schema.content
    )
    if not message:
        await connection_manager.send_error("Message not created", ws)
        return
    
    await invalidate_cache(r, REDIS_MESSAGES_KEY, chat.uuid)
    await add_message_to_elastic(
        es, message.uuid, current_user.uuid, chat.uuid, message.content
    )

    await add_chat_to_new_folder_for_all(db, current_user, chat) 
    await delete_cache_for_users(r, chat, current_user)

    send_message_schema = SendMessageSchema(
        uuid=message.uuid, user_uuid=current_user.uuid,
        chat_uuid=chat.uuid, content=message.content,
        created_at=message.created_at, updated_at=message.updated_at
    )
    outgoing_message: dict = send_message_schema.model_dump(mode="json")
    outgoing_message["type"] = "new_message"
    await connection_manager.broadcast_to_chat(chat.uuid, outgoing_message)

    logger.info(f"Message was sent ({message.uuid})")

@connection_manager.handler("read_message")
async def read_message_handler(
    db: AsyncSession,
    r: Redis,
    ws: WebSocket,
    current_user: UserModel,
    incomming_message: dict,
    **kwargs,
):
    message_read_schema = ChatActionSchema(**incomming_message)

    # checks if chat exists
    chat = await get_chat_or_none(db, message_read_schema.chat_uuid)
    if not chat:
        await connection_manager.send_error("Chat not found", ws)
        return

    await mark_chat_read(db, current_user, chat)

    await remove_chat_from_new_folder(db, current_user, chat)
    await invalidate_cache(r, REDIS_FOLDERS_KEY, current_user.uuid)

    outgoing_message: dict = message_read_schema.model_dump(mode="json")
    outgoing_message["user_uuid"] = str(current_user.uuid)
    await connection_manager.broadcast_to_chat(chat.uuid, outgoing_message)

    logger.info(f"Messages were read ({current_user.uuid})")

@connection_manager.handler("join_chat")
async def join_chat_handler(
    db: AsyncSession,
    ws: WebSocket,
    current_user: UserModel,
    incomming_message: dict,
    **kwargs,
):
    """ Updates websockets connected to chat. E.g. user joins a new chat. """
    join_chat_schema = ChatActionSchema(**incomming_message)
    
    chat = await get_chat_or_none(db, join_chat_schema.chat_uuid)
    if not chat:
        await connection_manager.send_error("Chat not found", ws)
        return
    
    if not is_user_in_chat(current_user, chat):
        await connection_manager.send_error("Chat not found", ws)
        return
    
    await connection_manager.add_user_to_chat(join_chat_schema.chat_uuid, ws)
    

@connection_manager.handler("quit_chat")
async def quit_chat_handler(
    ws: WebSocket,
    incomming_message: dict,
    **kwargs,
):
    join_chat_schema = ChatActionSchema(**incomming_message)
    
    # no checks needed
    
    await connection_manager.remove_user_from_chat(join_chat_schema.chat_uuid, ws)