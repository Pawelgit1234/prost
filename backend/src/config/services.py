from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from elasticsearch import AsyncElasticsearch
from fastapi import HTTPException, status

from src.settings import ELASTIC_CHATS_INDEX_NAME, ELASTIC_USERS_INDEX_NAME
from src.chats.models import ChatModel
from src.auth.models import UserModel
from src.chats.enums import ChatType
from src.chats.utils import ensure_user_in_chat_or_403
from src.config.schemas import UserConfigSchema, GroupConfigSchema

async def update_user_config_in_db(
    db: AsyncSession,
    user: UserModel,
    user_config: UserConfigSchema
) -> None:
    user.first_name = user_config.first_name
    user.last_name = user_config.last_name
    user.username = user_config.username
    user.description = user_config.description
    user.is_visible = user_config.is_visible
    user.is_open_for_messages = user_config.is_open_for_messages
    user.avatar = user_config.avatar_url
    await db.commit()

async def update_user_config_in_elastic(
    es: AsyncElasticsearch,
    user_config: UserConfigSchema,
    old_username: str,
    user_uuid: UUID
) -> None:
    await es.update(
        index=ELASTIC_USERS_INDEX_NAME,
        id=str(user_uuid),
        doc={
            "first_name": user_config.first_name,
            "last_name": user_config.last_name,
            "username": user_config.username,
            "description": user_config.description,
            "is_visible": user_config.is_visible,
            "is_open_for_messages": user_config.is_open_for_messages,
            "avatar": user_config.avatar_url
        }
    )

    if old_username == user_config.username:
        return
    
    # for private chats to
    await es.update_by_query(
        index=ELASTIC_CHATS_INDEX_NAME,
        query={
            "term": {
                "user_names.keyword": old_username
            }
        },
        script={
            "source": """
                if (ctx._source.user_names != null) {
                    for (int i = 0; i < ctx._source.user_names.size(); i++) {
                        if (ctx._source.user_names[i] == params.old) {
                            ctx._source.user_names[i] = params.new;
                        }
                    }
                }
            """,
            "params": {
                "old": old_username,
                "new": user_config.username,
            }
        }
    )

async def update_group_config_in_db(
    db: AsyncSession,
    group: ChatModel,
    user: UserModel,
    group_config: GroupConfigSchema
) -> None:
    ensure_user_in_chat_or_403(user, group)
    if group.chat_type != ChatType.GROUP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This must be a group"
        )

    group.name = group_config.name
    group.description = group_config.description
    group.is_open_for_messages = group_config.is_open_for_messages
    group.is_visible = group_config.is_visible
    group.avatar = group_config.avatar_url
    await db.commit()

async def update_group_config_in_elastic(
    es: AsyncElasticsearch,
    group_config: GroupConfigSchema
) -> None:
    await es.update(
        index=ELASTIC_CHATS_INDEX_NAME,
        id=str(group_config.uuid),
        doc={
            "name": group_config.name,
            "description": group_config.description,
            "is_open_for_messages": group_config.is_open_for_messages,
            "is_visible": group_config.is_visible,
            "avatar": group_config.avatar_url
        }
    )