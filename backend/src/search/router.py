from typing import Annotated
import logging

from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from elasticsearch import AsyncElasticsearch

from src.settings import REDIS_FOLDERS_KEY, REDIS_CHATS_KEY, \
    REDIS_CACHE_EXPIRE_SECONDS, ELASTIC_PAGE_SIZE, ELASTIC_CHATS_INDEX_NAME
from src.database import get_es, get_redis
from src.utils import invalidate_cache
from src.dependencies import get_active_current_user
from src.auth.models import UserModel
    
logger = logging.getLogger(__name__)

router = APIRouter(prefix='/search', tags=['search'])

@router.get('/chats')
async def search_chats(
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
    r: Annotated[Redis, Depends(get_redis)],
    # current_user: Annotated[UserModel, Depends(get_active_current_user)],
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
):

    body = {
        "query": {
            "multi_match": {
                "query": q,
                "fields": ["name^5", "description^0.5"] # name is more important than description
            }
        },
        "from": (page - 1) * ELASTIC_PAGE_SIZE,
        "size": ELASTIC_PAGE_SIZE
    }
    
    response = await es.search(index=ELASTIC_CHATS_INDEX_NAME, body=body)
    hits = response["hits"]["hits"]
    
    items = [hit["_source"] for hit in hits]
    total = response["hits"]["total"]["value"]

    return {
        "total": total,
        "page": page,
        "page_size": ELASTIC_PAGE_SIZE,
        "items": items
    }

# @router.get('/messages')
# async def search_messages(
#     r: Annotated[Redis, Depends(get_redis)],
#     current_user: Annotated[UserModel, Depends(get_active_current_user)],
#     q: str,
# ):
#     return None