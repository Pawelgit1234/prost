from typing import Iterable, Any
import json

from src.join_requests.schemas import JoinRequestSchema

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
