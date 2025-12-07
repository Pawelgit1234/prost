from uuid import UUID
import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, delete, insert
from sqlalchemy.orm import selectinload

from src.utils import save_to_db
from src.auth.models import UserModel
from src.chats.models import ChatModel
from src.folders.models import FolderModel, FolderChatAssociationModel
from src.folders.schemas import CreateFolderSchema, FolderOrderSchema
from src.folders.enums import FolderType

logger = logging.getLogger(__name__)

# already protects the user with by checking the user id
async def get_folder_chat_assoc_or_404(
    db: AsyncSession,
    user: UserModel,
    folder_uuid: UUID,
    chat_uuid: UUID,
    detail: str = "Association not found",
) -> FolderChatAssociationModel:
    result = await db.execute(
        select(FolderChatAssociationModel)
        .options(selectinload(FolderChatAssociationModel.folder))
        .join(FolderModel, FolderChatAssociationModel.folder_id == FolderModel.id)
        .join(ChatModel, FolderChatAssociationModel.chat_id == ChatModel.id)
        .where(
            and_(
                FolderModel.uuid == folder_uuid,
                ChatModel.uuid == chat_uuid,
                FolderModel.user_id == user.id,
            )
        )
    )
    assoc = result.scalar_one_or_none()

    if assoc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    return assoc


async def get_folders_list(db: AsyncSession, user: UserModel) -> list[FolderModel]:
    result = await db.execute(
        select(FolderModel)
        .options(
            selectinload(FolderModel.chat_associations).selectinload(
                FolderChatAssociationModel.chat
            )
        )
        .where(FolderModel.user_id == user.id)
        .order_by(FolderModel.position)
    )
    return result.scalars().all()


# async def get_chats_list_from_folder(
#     db: AsyncSession,
#     user: UserModel,
#     folder_uuid: UUID
# ) -> list[ChatSchema]:
#     result = await db.execute(
#         select(FolderModel.user_id, ChatModel, FolderChatAssociationModel.is_pinned)
#         .join(FolderChatAssociationModel, ChatModel.id == FolderChatAssociationModel.chat_id)
#         .join(FolderModel, FolderChatAssociationModel.folder_id == FolderModel.id)
#         .where(FolderModel.uuid == folder_uuid)
#     )
#     rows = result.all()
#
#     # checks if this folder belongs to the user
#     if rows[0][0] != user.id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Access to Folder forbidden"
#         )
#
#     return [
#         ChatSchema.model_validate({
#             **chat.__dict__,
#             "is_pinned": is_pinned
#         })
#         for _, chat, is_pinned in rows
#     ]


async def get_last_position(db: AsyncSession, user: UserModel) -> int:
    result = await db.execute(
        select(FolderModel.position)
        .where(FolderModel.user_id == user.id)
        .order_by(desc(FolderModel.position))
        .limit(1)
    )
    return result.scalar_one_or_none() or 0


async def reorder_folders_after_deletion(db: AsyncSession, user: UserModel) -> None:
    folders = await get_folders_list(db, user)

    for new_pos, folder in enumerate(folders):
        folder.position = new_pos
    await db.commit()

async def create_folder_in_db(
    db: AsyncSession,
    user: UserModel,
    folder_info: CreateFolderSchema | None = None,
    folder_type: FolderType | None = FolderType.CUSTOM,
) -> FolderModel:
    last_position = await get_last_position(db, user)

    folder = FolderModel(
        name=None if folder_info is None else folder_info.name,
        position=last_position + 1,
        user=user,
        folder_type=folder_type,
    )

    return (await save_to_db(db, [folder]))[0]


async def delete_folder_in_db(
    db: AsyncSession, user: UserModel, folder: FolderModel
) -> None:
    if folder.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your folder"
        )

    if folder.folder_type != FolderType.CUSTOM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only custom folders allowed"
        )

    await db.delete(folder)
    await db.commit()
    await reorder_folders_after_deletion(db, user)
    logger.info(f"Folder {folder.name} deleted by {user.username}")


async def rename_folder_in_db(
    db: AsyncSession, user: UserModel, folder: FolderModel, new_name: str
) -> None:
    if folder.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your folder"
        )

    if folder.folder_type != FolderType.CUSTOM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only custom folders allowed"
        )

    folder.name = new_name
    await db.commit()

async def replace_chats_in_db(
    db: AsyncSession, user: UserModel, folder: FolderModel, chat_uuids: list[UUID]
) -> None:
    if folder.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your folder"
        )

    if folder.folder_type != FolderType.CUSTOM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only custom folders allowed"
        )

    # get current chat ids
    current_chat_ids = set(
        await db.scalars(
            select(FolderChatAssociationModel.chat_id).where(
                FolderChatAssociationModel.folder_id == folder.id
            )
        )
    )

    # get ids from chat uuids
    result = await db.execute(
        select(ChatModel.id).where(ChatModel.uuid.in_(chat_uuids))
    )
    new_chat_ids = {i[0] for i in result.all()}

    # calculates diff
    to_add = new_chat_ids - current_chat_ids
    to_remove = current_chat_ids - new_chat_ids

    if to_remove:
        await db.execute(
            delete(FolderChatAssociationModel).where(
                FolderChatAssociationModel.folder_id == folder.id,
                FolderChatAssociationModel.chat_id.in_(to_remove),
            )
        )

    if to_add:
        await db.execute(
            insert(FolderChatAssociationModel),
            [{"folder_id": folder.id, "chat_id": cid} for cid in to_add],
        )

    await db.commit()

async def delete_chat_from_folder(
    db: AsyncSession,
    assoc: FolderChatAssociationModel
) -> None:
    if assoc.folder.folder_type != FolderType.CUSTOM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only custom folders allowed"
        )

    await db.delete(assoc)
    await db.commit()

async def order_folders_in_db(
    db: AsyncSession,
    user: UserModel,
    folders: list[FolderOrderSchema]
) -> None:
    position_map = {f.uuid: f.position for f in folders}

    result = await db.execute(
        select(FolderModel)
        .where(
            and_(
                FolderModel.uuid.in_(position_map.keys()),
                FolderModel.user_id == user.id
            )
        )
    )

    folder_models = result.scalars().all()

    if len(folder_models) != len(position_map):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Some folders are not yours"
        )

    for folder in folder_models:
        folder.position = position_map[folder.uuid]

    await db.commit()
