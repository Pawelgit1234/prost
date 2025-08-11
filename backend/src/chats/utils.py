import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from elasticsearch import AsyncElasticsearch
from redis.asyncio import Redis
from fastapi import HTTPException, status

from src.settings import REDIS_CHATS_KEY, ELASTIC_CHATS_INDEX_NAME
from src.utils import invalidate_cache
from src.auth.models import UserModel
from src.folders.models import FolderModel
from src.folders.enums import FolderType
from src.chats.models import ChatModel
from src.chats.enums import ChatType

def group_folders_by_type(folders: list[FolderModel]) -> dict[FolderType, FolderModel]:
    return {f.folder_type: f for f in folders}

async def invalidate_chat_cache(r: Redis, *folders: FolderModel, user: UserModel):
    await asyncio.gather(*[
        invalidate_cache(r, REDIS_CHATS_KEY, folder.uuid, user.uuid) for folder in folders
    ])

def get_group_users_uuids(chat: ChatModel) -> list[str]:
    return [str(assoc.user.uuid) for assoc in chat.user_associations]

def is_user_in_chat(user: UserModel, chat: ChatModel) -> bool:
    return user.id in [assoc.user_id for assoc in chat.user_associations]

async def get_common_chats(
    db: AsyncSession,
    user: UserModel,
    other_user: UserModel
) -> list[ChatModel]:
    user_chat_ids = [assoc.chat_id for assoc in user.chat_associations]
    other_user_chat_ids = [assoc.chat_id for assoc in other_user.chat_associations]
    common_chat_ids = list(set(user_chat_ids) & set(other_user_chat_ids)) # [1, 2, 3] & [2, 3, 4] => [2, 3]
    result = await db.execute(select(ChatModel).where(ChatModel.id.in_(common_chat_ids)))
    return result.scalars().all()

async def ensure_no_normal_chat_or_403(
    db: AsyncSession,
    user: UserModel,
    other_user: UserModel,
    detail: str = 'You already have a normal chat with user'
) -> None:
    common_chats = await get_common_chats(db, user, other_user)
    chat_types = [chat.chat_type for chat in common_chats]
    if ChatType.NORMAL in chat_types:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )
    
def ensure_user_in_chat_or_403(
    user: UserModel,
    chat: ChatModel,
    detail: str = "You must be in the chat"
):
    if not is_user_in_chat(user, chat):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

async def update_group_members_in_elastic(es: AsyncElasticsearch, chat: ChatModel) -> None:
    await es.update(
        index=ELASTIC_CHATS_INDEX_NAME,
        id=str(chat.uuid),
        doc={
            "members": get_group_users_uuids(chat),
        }
    )
