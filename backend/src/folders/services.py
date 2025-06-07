from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from src.utils import save_to_db
from src.auth.models import UserModel
from src.folders.models import FolderModel
from src.folders.schemas import CreateFolderSchema
from src.folders.enums import FolderType

async def get_folder_or_404(db: AsyncSession, folder_uuid: UUID):
    result = await db.execute(
        select(FolderModel)
        .where(FolderModel.uuid == folder_uuid)
        .options(selectinload(FolderModel.chats))
    )
    folder = result.scalar_one_or_none()

    if folder is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Folder not found')
    return folder

async def get_all_folders(db: AsyncSession, user: UserModel) -> list[FolderModel]:
    result = await db.execute(
        select(FolderModel)
        .where(FolderModel.user_id == user.id)
        .order_by(FolderModel.position)
    )
    return await result.all()

async def get_all_chats_from_folder(db: AsyncSession):
    pass

async def get_last_position(db: AsyncSession, user: UserModel) -> int:
    result = await db.execute(
        select(FolderModel.position)
        .where(FolderModel.user_id == user.id)
        .order_by(desc(FolderModel.position))
        .limit(1)
    )
    return result.scalar_one_or_none() or 0

async def reorder_folders_after_deletion(db: AsyncSession, user: UserModel) -> None:
    result = await db.execute(
        select(FolderModel)
        .where(FolderModel.user_id == user.id)
        .order_by(FolderModel.position)
    )
    folders = result.scalar_one_or_none()

    if folders is not None:
        for new_pos, folder in enumerate(folders):
            folder.position = new_pos
        await db.commit()

async def create_folder_in_db(
    db: AsyncSession,
    user: UserModel,
    folder_info: CreateFolderSchema
) -> FolderModel:
    last_position = await get_last_position()
    folder = FolderModel(
        name=folder_info.name, position=last_position + 1,
        user=user, folder_type=FolderType.CUSTOM
    )
    return (await save_to_db(db, [folder]))[0]

async def delete_folder_in_db(db: AsyncSession, folder_uuid: UUID) -> None:
    folder = await get_folder_or_404(db, folder_uuid)
    await db.delete(folder)
    await db.commit()
