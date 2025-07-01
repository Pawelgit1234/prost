from typing import Annotated
import logging

from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from elasticsearch import AsyncElasticsearch
from sqlalchemy.ext.asyncio import AsyncSession

from src.settings import ELASTIC_PAGE_SIZE, REDIS_SEARCH_HISTORY_KEY, SEARCH_HISTORY_SIZE, \
    ELASTIC_CHATS_INDEX_NAME, ELASTIC_USERS_INDEX_NAME, ELASTIC_MESSAGES_INDEX_NAME
from src.database import get_es, get_redis, get_db
from src.dependencies import get_active_current_user
from src.auth.models import UserModel
    
logger = logging.getLogger(__name__)

router = APIRouter(prefix='/search', tags=['search'])

# users, groups, messages + own chats
@router.get('/global')
async def search_global(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
):
    key = REDIS_SEARCH_HISTORY_KEY.format(current_user.uuid)
    await r.lpush(key, q)
    await r.ltrim(key, 0, SEARCH_HISTORY_SIZE - 1)

    response = await es.search(
        index=f'{ELASTIC_USERS_INDEX_NAME},{ELASTIC_CHATS_INDEX_NAME},{ELASTIC_MESSAGES_INDEX_NAME}',
        body={
            'query': {
                'multi_match': {
                    'query': q,
                    'fields': [
                        'name^5', 'name.autocomplete^3',
                        'username^4', 'username.autocomplete^2',
                        'first_name^2', 'first_name.autocomplete',
                        'last_name^2', 'last_name.autocomplete',
                        'description^0.5',
                        'text', 'text.autocomplete',
                    ],
                    'type': 'best_fields',
                    'fuzziness': 'AUTO',
                }
            },
            'from': (page - 1) * ELASTIC_PAGE_SIZE,
            'size': ELASTIC_PAGE_SIZE
        }
    )

    total = response['hits']['total']['value']
    items: list[dict] = []

    for hit in response['hits']['hits']:
        doc = hit['_source']
        doc['uuid'] = hit['_id']
        doc['type'] = hit['_index']
        items.append(doc)
    
    return {
        "total": total,
        "page": page,
        "items": items
    }

@router.get('/messages')
async def search_messages(
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    q: str,
):
    return None

# n last search queries
@router.get('/history')
async def get_search_history(
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
):
    history = await r.lrange(REDIS_SEARCH_HISTORY_KEY.format(current_user.uuid), 0, -1)
    return {'items': history}
