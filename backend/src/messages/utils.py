from uuid import UUID

from elasticsearch import AsyncElasticsearch
from redis.asyncio import Redis

from src.settings import ELASTIC_MESSAGES_INDEX_NAME, REDIS_FOLDERS_KEY
from src.utils import invalidate_cache
from src.messages.models import MessageModel, ReadStatusModel
from src.messages.schemas import SendMessageSchema
from src.chats.models import ChatModel
from src.auth.models import UserModel

def message_model_to_schema(message: MessageModel) -> SendMessageSchema:
    return SendMessageSchema(
        message_uuid=message.uuid,
        created_at=message.created_at,
        updated_at=message.updated_at,
        user_uuid=message.user_id,
        chat_uuid=message.chat_id,
        content=message.content
    )

async def create_read_statuses_for_all_chat_users(
    sender_user: UserModel,
    chat: ChatModel,
    message: MessageModel,
) -> list[ReadStatusModel]:
    """
    Creates ReadStatus rows for every user in chat except sender.
    """

    statuses: list[ReadStatusModel] = []

    for assoc in chat.user_associations:
        user = assoc.user

        if user.id == sender_user.id:
            continue

        status = ReadStatusModel(
            user_id=user.id,
            message_id=message.id,
            is_read=False,
        )

        statuses.append(status)

    return statuses

async def add_message_to_elastic(
    es: AsyncElasticsearch,
    message_uuid: UUID,
    user_uuid: UUID,
    chat_uuid: UUID,
    content: str   
) -> None:
    await es.index(
        index=ELASTIC_MESSAGES_INDEX_NAME,
        id=str(message_uuid),
        document={
            "user": str(user_uuid),
            "chat": str(chat_uuid),
            "content": content,
        }
    )

async def delete_cache_for_users(
    r: Redis,
    chat: ChatModel,
    sender_user: UserModel
) -> None:
    user_uuids = [
        assoc.user.uuid
        for assoc in chat.user_associations
        if assoc.user.uuid != sender_user.uuid
    ]

    keys = [REDIS_FOLDERS_KEY.format(u) for u in user_uuids]
    if keys:
        await r.delete(*keys)