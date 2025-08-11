from typing import Iterable, Any
import json
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.utils import get_object_or_404
from src.chats.models import ChatModel
from src.join_requests.schemas import JoinRequestSchema
from src.join_requests.models import JoinRequestModel


def serialize_join_request_model_list(models: Iterable[Any]) -> list[dict]:
    result = []
    for obj in models:
        result.append(json.loads(JoinRequestSchema(
            uuid=obj.uuid,
            join_request_type=obj.join_request_type,
            target_uuid=obj.group.uuid if obj.group else obj.receiver_user.uuid,
            sender_user_uuid=obj.sender_user.uuid,
        ).model_dump_json()))
    return result

async def get_join_request_or_404(db: AsyncSession, join_request_uuid: UUID) -> JoinRequestModel:
    join_request = await get_object_or_404(
        db, JoinRequestModel, JoinRequestModel.uuid == join_request_uuid,
        detail='Join request not found',
        options=[
            selectinload(JoinRequestModel.sender_user),
            selectinload(JoinRequestModel.group).selectinload(ChatModel.user_associations)
        ]
    )