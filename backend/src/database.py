import logging
import asyncio

from sqlalchemy.orm import DeclarativeBase, selectinload
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis
from elasticsearch import AsyncElasticsearch, exceptions
from elasticsearch.helpers import async_bulk

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
async def wait_for_elasticsearch(es: AsyncElasticsearch, retries: int = 30, delay: float = 1.0):
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

# no need for production
async def sync_db_to_elastic(db: AsyncSession, es: AsyncElasticsearch) -> None:
    from src.auth.models import UserModel
    from src.chats.models import ChatModel, UserChatAssociationModel
    from src.chats.enums import ChatType
    from src.chats.utils import get_group_users_uuids

    logger.info("Starting full synchronization...")

    result = await db.execute(select(UserModel))
    users = result.scalars().all()

    if users:
        user_actions = [
            {
                "_index": ELASTIC_USERS_INDEX_NAME,
                "_id": str(user.uuid),
                "_source": {
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "username": user.username,
                    "description": user.description,
                    "avatar": user.avatar,
                    "is_open_for_messages": user.is_open_for_messages,
                    "is_visible": user.is_visible,
                    "is_active": user.is_active,
                }
            } for user in users
        ]
        await async_bulk(es, user_actions)
        logger.info(f"Synced {len(users)} users.")

    result = await db.execute(
        select(ChatModel)
        .options(
            selectinload(ChatModel.user_associations)
            .selectinload(UserChatAssociationModel.user),
        )
    )
    chats = result.scalars().all()

    if chats:
        chat_actions = []
        for chat in chats:
            user_names = None
            if chat.chat_type == ChatType.NORMAL:
                user_names = [assoc.user.username for assoc in chat.user_associations]

            chat_actions.append({
                "_index": ELASTIC_CHATS_INDEX_NAME,
                "_id": str(chat.uuid),
                "_source": {
                    "chat_type": chat.chat_type.value,
                    "name": chat.name if chat.chat_type == ChatType.GROUP else None,
                    "description": chat.description,
                    "avatar": chat.avatar, 
                    "members": get_group_users_uuids(chat),
                    "user_names": user_names,
                    "is_visible": chat.is_visible,
                    "is_open_for_messages": chat.is_open_for_messages,
                }
            })
        
        await async_bulk(es, chat_actions)
        logger.info(f"Synced {len(chats)} chats.")

    # TODO: Message sync

    logger.info("Full synchronization complete!")


async def create_indices(es: AsyncElasticsearch):
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
                        "is_open_for_messages": {"type": "boolean"}, # always false in normal chats
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
                        "user_names": { # only for normal chats
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
                        "is_open_for_messages": {"type": "boolean"},
                        "is_visible": {"type": "boolean"},
                        "is_active": {"type": "boolean"},
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
