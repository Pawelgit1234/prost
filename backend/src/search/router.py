from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from elasticsearch import AsyncElasticsearch

from src.settings import ELASTIC_PAGE_SIZE, REDIS_SEARCH_HISTORY_KEY, \
    ELASTIC_CHATS_INDEX_NAME, ELASTIC_USERS_INDEX_NAME, ELASTIC_MESSAGES_INDEX_NAME
from src.database import get_es, get_redis
from src.dependencies import get_active_current_user
from src.auth.models import UserModel
from src.search.utils import add_query_to_history, parse_elastic_response

router = APIRouter(prefix='/search', tags=['search'])

# users, groups, messages + own chats
@router.get('/global')
async def search_global(
    r: Annotated[Redis, Depends(get_redis)],
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    q: str = Query(..., min_length=1, max_length=100),
    page: int = Query(1, ge=1),
):
    await add_query_to_history(r, current_user.uuid, q)

    response = await es.search(
        index=f'{ELASTIC_USERS_INDEX_NAME},{ELASTIC_CHATS_INDEX_NAME},{ELASTIC_MESSAGES_INDEX_NAME}',
        body={
            "query": {
                "bool": {
                    "must": {
                        "multi_match": {
                            "query": q,
                            "fields": [
                                'name^5', 'name.autocomplete^3',
                                'username^4', 'username.autocomplete^2',
                                'first_name^2', 'first_name.autocomplete',
                                'last_name^2', 'last_name.autocomplete',
                                'description^0.5',
                                'text', 'text.autocomplete',
                            ],
                            "type": "best_fields",
                            "fuzziness": "AUTO"
                        }
                    },
                    "filter": {
                        "bool": {
                            "should": [
                                # All users are public by default
                                { "term": { "_index": ELASTIC_USERS_INDEX_NAME } },

                                # Chats: show if is_visible OR user is a member
                                {
                                    "bool": {
                                        "must": [
                                            { "term": { "_index": ELASTIC_CHATS_INDEX_NAME } },
                                            {
                                                "bool": {
                                                    "should": [
                                                        { "term": { "is_visible": True } },
                                                        { "term": { "members": str(current_user.uuid) } }
                                                    ]
                                                }
                                            }
                                        ]
                                    }
                                },

                                # Messages: only visible to participants
                                {
                                    "bool": {
                                        "must": [
                                            { "term": { "_index": ELASTIC_MESSAGES_INDEX_NAME } },
                                            { "term": { "members": str(current_user.uuid) } }
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                }
            },
            "from": (page - 1) * ELASTIC_PAGE_SIZE,
            "size": ELASTIC_PAGE_SIZE
        }
    )

    total, items = parse_elastic_response(response, current_user.uuid)
    
    return {
        "total": total,
        "page": page,
        "page_size": ELASTIC_PAGE_SIZE,
        "items": items
    }

@router.get('/messages')
async def search_messages(
    r: Annotated[Redis, Depends(get_redis)],
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    chat_uuid: UUID,
    q: str = Query(..., min_length=1, max_length=100),
    page: int = Query(1, ge=1),
):
    await add_query_to_history(r, current_user.uuid, q)

    response = await es.search(
        index=f'{ELASTIC_MESSAGES_INDEX_NAME}',
        body={
            "query": {
                "bool": {
                    "must": {
                        "multi_match": {
                            "query": q,
                            "fields": [
                                'text', 'text.autocomplete',
                            ],
                            "type": "best_fields",
                            "fuzziness": "AUTO"
                        }
                    },
                    "filter": {
                        # Messages: only visible to participants
                        "bool": {
                            "must": [
                                { "term": { "members": str(current_user.uuid) } },
                                { "term": { "chat": chat_uuid } },
                            ]
                        }
                    }
                }
            },
            "from": (page - 1) * ELASTIC_PAGE_SIZE,
            "size": ELASTIC_PAGE_SIZE
        }
    )

    total, items = parse_elastic_response(response)
    
    return {
        "total": total,
        "page": page,
        "page_size": ELASTIC_PAGE_SIZE,
        "items": items
    }

# last search queries
@router.get('/history')
async def get_search_history(
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
):
    history = await r.lrange(REDIS_SEARCH_HISTORY_KEY.format(current_user.uuid), 0, -1)
    return {'items': history}
