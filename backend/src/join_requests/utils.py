from uuid import UUID

from redis.asyncio import Redis

from src.utils import invalidate_cache
from src.settings import REDIS_USER_JOIN_REQUESTS_KEY, REDIS_GROUP_JOIN_REQUESTS_KEY
from src.join_requests.enums import JoinRequestType
from src.join_requests.models import JoinRequestModel

async def invalidate_cache_specific(
    r: Redis,
    join_request: JoinRequestModel
) -> None:
    if join_request.join_request_type == JoinRequestType.USER:
        await invalidate_cache(r, REDIS_USER_JOIN_REQUESTS_KEY, join_request.receiver_user.uuid)
    elif join_request.join_request_type == JoinRequestType.GROUP:
        await invalidate_cache(r, REDIS_GROUP_JOIN_REQUESTS_KEY, join_request.group.uuid)