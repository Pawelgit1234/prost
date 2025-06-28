import logging
import asyncio

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from redis.asyncio import Redis
from elasticsearch import AsyncElasticsearch, exceptions

from src.settings import DATABASE_URL, REDIS_PORT, REDIS_HOST, ELASTIC_PASSWORD, \
    ELASTIC_CHATS_INDEX_NAME, ELASTIC_MESSAGES_INDEX_NAME, ELASTIC_USERS_INDEX_NAME, ELASTIC_HOST

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session

redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

async def get_redis():
    try:
        yield redis_client
    finally:
        pass

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
    raise RuntimeError("Elasticsearch did not become available in time.")
   
async def create_indices():
    await _wait_for_elasticsearch(es)
    try:
        # chats
        if not await es.indices.exists(index=ELASTIC_CHATS_INDEX_NAME):
            await es.indices.create(
                index=ELASTIC_CHATS_INDEX_NAME,
                body={
                    "mappings": {
                        "properties": {
                            "uuid": {"type": "keyword"},
                            "chat_type": {"type": "keyword"},
                            "name": {"type": "text"},
                            "description": {"type": "text"},
                            "avatar": {"type": "keyword", "index": False},
                        }
                    }
                }
            )
            logger.info(f"Elasticsearch index '{ELASTIC_CHATS_INDEX_NAME}' created")

        # users
        if not await es.indices.exists(index=ELASTIC_USERS_INDEX_NAME):
            await es.indices.create(
                index=ELASTIC_USERS_INDEX_NAME,
                body={
                    "mappings": {
                        "properties": {
                            "uuid": {"type": "keyword"},
                            "first_name": {"type": "text"},
                            "last_name": {"type": "text"},
                            "username": {"type": "text"},
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
                    "mappings": {
                        "properties": {
                            "uuid": {"type": "keyword"},
                            "text": {"type": "text"},
                        }
                    }
                }
            )
            logger.info(f"Elasticsearch index '{ELASTIC_MESSAGES_INDEX_NAME}' created")

    except Exception as e:
        logger.warning(f"Elastic error: {e}")
