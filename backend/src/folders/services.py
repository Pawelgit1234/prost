from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import UserModel
from src.folders.models import FolderModel

async def create_folder_in_db(
    db: AsyncSession,
    current_user: UserModel,
) -> FolderModel:
    pass