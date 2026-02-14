from typing import Annotated
import json
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from elasticsearch import AsyncElasticsearch
from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect

from src.settings import REDIS_MESSAGES_KEY, REDIS_CACHE_EXPIRE_SECONDS
from src.database import get_db, get_redis, get_es
from src.utils import wrap_list_response
from src.dependencies import get_active_current_user
from src.auth.models import UserModel
from src.chats.services import get_all_chats_with_last_message
from src.messages.handlers import connection_manager
from src.messages.services import get_all_message_schemas

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
    ws: WebSocket,
    current_user: Annotated[UserModel, Depends(get_active_current_user)]
):
    # accept websocket
    await connection_manager.connect_socket(ws)
    logger.info("Websocket connection is established")

    # add to connection manager
    await connection_manager.add_user_socket_connection(current_user.uuid, ws)

    # add to chats
    chats = await get_all_chats_with_last_message(db, current_user)
    for chat, _ in chats:
        await connection_manager.add_user_to_chat(chat.uuid, ws)

    try:
        while True:
            try:
                incoming_message = await ws.receive_json()

                message_type = incoming_message.get("type")
                if not message_type:
                    await connection_manager.send_error("Wrong message format", ws)
                    continue
                    
                handler = connection_manager.handlers.get(message_type)
                if not handler:
                    await connection_manager.send_error(f"Type: {message_type} was not found", ws)
                    continue

                await handler(
                    db=db, r=r, es=es, ws=ws,
                    current_user=current_user,
                    incoming_message=incoming_message
                )

            except (json.JSONDecodeError, AttributeError) as excinfo:
                logger.exception(f"Websocket error, detail: {excinfo}")
                await connection_manager.send_error("Wrong message format", ws)
            except ValueError as excinfo:
                logger.exception(f"Websocket error, detail: {excinfo}")
                await connection_manager.send_error("Could not validate incoming message", ws)

    except WebSocketDisconnect:
        logger.info(f"{current_user.uuid} websocket disconnected")
        
        # remove from chats
        for chat, _ in chats:
            await connection_manager.remove_user_from_chat(chat.uuid, ws)
        
        # remove from connection manager
        await connection_manager.remove_user(current_user.uuid, ws)

# no lazy loading
@router.get('/messages/{chat_uuid}')
async def get_all_chat_messages(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    chat_uuid: UUID
): 
    redis_key = REDIS_MESSAGES_KEY.format(chat_uuid)
    if data := await r.get(redis_key):
        return json.loads(data)

    message_schemas = await get_all_message_schemas(db, current_user, chat_uuid)
    messages = [chat.model_dump() for chat in chats_schemas]
    data = wrap_list_response(messages)

    await r.set(
        redis_key,
        json.dumps(data, default=str),
        REDIS_CACHE_EXPIRE_SECONDS
    )

    return data