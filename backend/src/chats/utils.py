import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from src.settings import REDIS_CHATS_KEY
from src.utils import invalidate_cache
from src.auth.models import UserModel
from src.folders.models import FolderModel
from src.folders.enums import FolderType
from src.chats.models import ChatModel

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
    common_chat_ids = user_chat_ids & other_user_chat_ids # [1, 2, 3] & [2, 3, 4] => [2, 3]
    result = await db.execute(select(ChatModel).where(ChatModel.id.in_(common_chat_ids)))
    return result.scalars().all()
