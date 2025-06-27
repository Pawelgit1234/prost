import logging

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from redis.asyncio import Redis
from elasticsearch import AsyncElasticsearch

from src.settings import DATABASE_URL, REDIS_PORT, REDIS_HOST, ELASTIC_PASSWORD, \
    ELASTIC_CHATS_INDEX_NAME, ELASTIC_HOST

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

async def create_indices():
    # I do not know why, but the whole elasticsearch do not work without
    # this try/except. This is stupid.
    try:
        if not await es.indices.exists(index=ELASTIC_CHATS_INDEX_NAME):
            await es.indices.create(
                index=ELASTIC_CHATS_INDEX_NAME,
                body={
                    "mappings": {
                        "properties": {
                            "uuid": {"type": "text"},
                            "chat_type": {"type": "text"},
                            "name": {"type": "text"},
                            "description": {"type": "text"},
                            "avatar": {"type": "text"},
                        }
                    }
                }
            )

            logger.info(f"Elasticsearch index '{ELASTIC_CHATS_INDEX_NAME}' created")
    except Exception as e:
        logger.warning(f"Something went wrong: {e}")
