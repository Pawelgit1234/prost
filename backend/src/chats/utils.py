import asyncio

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

def get_chat_users_uuids(chat: ChatModel) -> list[str]:
    return [str(assoc.user.uuid) for assoc in chat.user_associations]