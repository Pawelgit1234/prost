from elasticsearch import AsyncElasticsearch

from src.messages.models import MessageModel
from src.messages.schemas import MessageSchema

def message_model_to_schema(message: MessageModel) -> MessageSchema:
    return MessageSchema(
        uuid=message.uuid,
        message_type=message.message_type,
        created_at=message.created_at,
        updated_at=message.updated_at,
    )