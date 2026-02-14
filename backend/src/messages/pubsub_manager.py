from uuid import UUID
import asyncio
import logging

from src.database import redis_client

logger = logging.getLogger(__name__)

class PubSubManager:
    def __init__(self):
        self.redis = redis_client
        self.pubsub = redis_client.pubsub()
        self.reader_task: asyncio.Task | None = None
    
    async def _reader_loop(self, on_message):
        try:
            while True:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True)
                if message:
                    await on_message(message)
        except Exception as e:
            logger.exception(f"Exception occurred: {e}")
    
    async def close(self):
        if self.reader_task:
            self.reader_task.cancel()
        await self.pubsub.close()

    async def subscribe(self, chat_uuid: UUID, on_message):
        await self.pubsub.subscribe(str(chat_uuid))

        if self.reader_task is None:
            self.reader_task = asyncio.create_task(
                self._reader_loop(on_message)
            )

    async def unsubscribe(self, chat_uuid: UUID):
        await self.pubsub.unsubscribe(str(chat_uuid))
    
    async def publish(self, chat_uuid: UUID, msg: str):
        await self.redis.publish(str(chat_uuid), msg)
