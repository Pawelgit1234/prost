from uuid import UUID
import json
import logging

from fastapi import WebSocket

from src.messages.pubsub_manager import PubSubManager

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.handlers: dict = {}
        self.chats: dict[UUID, set[WebSocket]] = {}
        self.user_uuid_to_ws: dict[UUID, set[WebSocket]] = {}
        self.pubsub = PubSubManager()

    def handler(self, message_type):
        def decorator(func):
            self.handlers[message_type] = func
            return func
        return decorator
    
    async def connect_socket(self, ws: WebSocket):
        await ws.accept()
    
    async def close(self):
        await self.pubsub.close()

    async def add_user_socket_connection(self, user_uuid: UUID, ws: WebSocket):
        self.user_uuid_to_ws.setdefault(user_uuid, set()).add(ws)
    
    async def add_user_to_chat(self, chat_uuid: UUID, ws: WebSocket):
        if chat_uuid in self.chats: # a.k.a. already subscribed
            self.chats[chat_uuid].add(ws)
        else:
            self.chats[chat_uuid] = {ws}
            await self.pubsub.subscribe(chat_uuid, self._on_pubsub_message)
    
    def remove_user(self, user_uuid: UUID, ws: WebSocket):
        if user_uuid in self.user_uuid_to_ws:
            self.user_uuid_to_ws[user_uuid].discard(ws) # remove if exists, else NO error

            if len(self.user_uuid_to_ws[user_uuid]) == 0:
                self.user_uuid_to_ws.pop(user_uuid)
    
    async def remove_user_from_chat(self, chat_uuid: UUID, ws: WebSocket):
        if chat_uuid in self.chats:
            self.chats[chat_uuid].discard(ws) # remove if exists, else NO error

            if len(self.chats[chat_uuid]) == 0:
                self.chats.pop(chat_uuid)
                await self.pubsub.unsubscribe(chat_uuid)

    async def _on_pubsub_message(self, message):
        chat_uuid = UUID(message["channel"].decode())
        data = message["data"].decode()

        sockets = self.chats.get(chat_uuid, set())
        for ws in sockets:
            await ws.send_text(data)

    async def send_error(self, message: str, websocket: WebSocket):
        await websocket.send_json({"status": "error", "message": message})
    
    async def broadcast_to_chat(self, chat_uuid: UUID, message: str | dict) -> None:
        if isinstance(message, dict):
            message = json.dumps(message)
        await self.pubsub.publish(chat_uuid, message)