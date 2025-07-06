import logging
import asyncio

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from redis.asyncio import Redis
from elasticsearch import AsyncElasticsearch, exceptions

from src.settings import DATABASE_URL, REDIS_PORT, REDIS_HOST, ELASTIC_PASSWORD, \
    ELASTIC_CHATS_INDEX_NAME, ELASTIC_MESSAGES_INDEX_NAME, ELASTIC_USERS_INDEX_NAME, ELASTIC_HOST

logger = logging.getLogger(__name__)

# SQLAlchemy
class Base(DeclarativeBase):
    pass

engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session

# Redis
redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

async def get_redis():
    try:
        yield redis_client
    finally:
        pass

# Elasticsearch
es = AsyncElasticsearch(
    ELASTIC_HOST,
    basic_auth=('elastic', ELASTIC_PASSWORD),
    verify_certs=False
)

async def get_es():
    try:
        yield es
    finally:
        pass

# workaround
async def _wait_for_elasticsearch(es: AsyncElasticsearch, retries: int = 30, delay: float = 1.0):
    for attempt in range(retries):
        try:
            if await es.ping():
                logger.info("Elasticsearch is available.")
                return
        except exceptions.ConnectionError:
            pass
        logger.info(f"Waiting for Elasticsearch... (attempt {attempt + 1}/{retries})")
        await asyncio.sleep(delay)
    logger.warning("Elasticsearch did not become available in time.")
    raise RuntimeError("Elasticsearch did not become available in time.")

async def create_indices():
    await _wait_for_elasticsearch(es)

    common_settings = {
        "settings": {
            "analysis": {
                "tokenizer": {
                    "autocomplete_tokenizer": {
                        "type": "edge_ngram",
                        "min_gram": 1,
                        "max_gram": 20,
                        "token_chars": ["letter", "digit"]
                    }
                },
                "analyzer": {
                    "autocomplete": {
                        "type": "custom",
                        "tokenizer": "autocomplete_tokenizer",
                        "filter": ["lowercase"]
                    }
                }
            }
        }
    }

    # chats
    if not await es.indices.exists(index=ELASTIC_CHATS_INDEX_NAME):
        await es.indices.create(
            index=ELASTIC_CHATS_INDEX_NAME,
            body={
                **common_settings,
                "mappings": {
                    "properties": {
                        "name": {
                            "type": "text",
                            "fields": {
                                "autocomplete": {
                                    "type": "text",
                                    "analyzer": "autocomplete",
                                    "search_analyzer": "standard"
                                }
                            }
                        },
                        "description": {"type": "text"},
                        "chat_type": {"type": "keyword"},
                        "members": {"type": "keyword"}, # users in chat
                        "is_visible": {"type": "boolean"}, # always false in normal chats
                        "avatar": {"type": "keyword", "index": False},
                    }
                }
            }
        )
        logger.info(f"Elasticsearch index '{ELASTIC_CHATS_INDEX_NAME}' created")

    # users
    # hidden user will not be saved
    if not await es.indices.exists(index=ELASTIC_USERS_INDEX_NAME):
        await es.indices.create(
            index=ELASTIC_USERS_INDEX_NAME,
            body={
                **common_settings,
                "mappings": {
                    "properties": {
                        "first_name": {
                            "type": "text",
                            "fields": {
                                "autocomplete": {
                                    "type": "text",
                                    "analyzer": "autocomplete",
                                    "search_analyzer": "standard"
                                }
                            }
                        },
                        "last_name": {
                            "type": "text",
                            "fields": {
                                "autocomplete": {
                                    "type": "text",
                                    "analyzer": "autocomplete",
                                    "search_analyzer": "standard"
                                }
                            }
                        },
                        "username": {
                            "type": "text",
                            "fields": {
                                "autocomplete": {
                                    "type": "text",
                                    "analyzer": "autocomplete",
                                    "search_analyzer": "standard"
                                }
                            }
                        },
                        "description": {"type": "text"},
                        "avatar": {"type": "keyword", "index": False},
                    }
                }
            }
        )
        logger.info(f"Elasticsearch index '{ELASTIC_USERS_INDEX_NAME}' created")

    # messages
    if not await es.indices.exists(index=ELASTIC_MESSAGES_INDEX_NAME):
        await es.indices.create(
            index=ELASTIC_MESSAGES_INDEX_NAME,
            body={
                **common_settings,
                "mappings": {
                    "properties": {
                        "text": {
                            "type": "text",
                            "fields": {
                                "autocomplete": {
                                    "type": "text",
                                    "analyzer": "autocomplete",
                                    "search_analyzer": "standard"
                                }
                            }
                        },
                        "chat": {"type": "keyword"}, # chat uuid
                        "members": {"type": "keyword"}, # users who see can see this msg
                    }
                }
            }
        )
        logger.info(f"Elasticsearch index '{ELASTIC_MESSAGES_INDEX_NAME}' created")
