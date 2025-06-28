from typing import Annotated
import logging

from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from elasticsearch import AsyncElasticsearch
from sqlalchemy.ext.asyncio import AsyncSession

from src.settings import ELASTIC_PAGE_SIZE, ELASTIC_CHATS_INDEX_NAME
from src.database import get_es, get_redis, get_db
from src.utils import invalidate_cache
from src.dependencies import get_active_current_user
from src.auth.models import UserModel
    
logger = logging.getLogger(__name__)

router = APIRouter(prefix='/search', tags=['search'])

@router.get('/global')
async def search_global(
    db: Annotated[AsyncSession, Depends(get_db)],
    r: Annotated[Redis, Depends(get_redis)],
    es: Annotated[AsyncElasticsearch, Depends(get_es)],
    # current_user: Annotated[UserModel, Depends(get_active_current_user)],
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
):

    body = {
        "query": {
            "multi_match": {
                "query": q,
                "fields": ["name", "description"] # name is more important than description
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

@router.get('/messages')
async def search_messages(
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
    q: str,
):
    return None

@router.get('/last_queries')
async def get_last_queries(
    r: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[UserModel, Depends(get_active_current_user)],
):
    return None