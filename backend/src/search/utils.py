from uuid import UUID

from redis.asyncio import Redis

from src.settings import REDIS_SEARCH_HISTORY_KEY, SEARCH_HISTORY_SIZE, ELASTIC_CHATS_INDEX_NAME

async def add_query_to_history(r: Redis, user_uuid: UUID, q: str) -> None:
    key = REDIS_SEARCH_HISTORY_KEY.format(user_uuid)
    await r.lrem(key, 0, q)
    await r.lpush(key, q)
    await r.ltrim(key, 0, SEARCH_HISTORY_SIZE - 1)

def parse_elastic_response(response: dict, user_uuid: UUID = None) -> tuple[int, list[dict]]:
    total = response['hits']['total']['value']

    items: list[dict] = []
    for hit in response['hits']['hits']:
        doc = hit['_source']
        doc['uuid'] = hit['_id']
        doc['type'] = hit['_index']

        # Indicates if current user is a member of the chat (for UI purposes)
        if user_uuid is not None and hit['_index'] == ELASTIC_CHATS_INDEX_NAME:
            doc['is_yours'] = str(user_uuid) in doc.get('members', [])

        items.append(doc)
    
    return total, items
    