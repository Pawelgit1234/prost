from uuid import UUID
import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, desc, and_
from sqlalchemy.orm import selectinload

from src.utils import save_to_db
from src.auth.models import UserModel
from src.chats.models import ChatModel
from src.chats.utils import is_user_in_chat
from src.folders.models import FolderModel, FolderChatAssociationModel
from src.folders.schemas import CreateFolderSchema
from src.folders.enums import FolderType

logger = logging.getLogger(__name__)

# already protects the user with by checking the user id
async def get_folder_chat_assoc_or_404(
    db: AsyncSession,
    user: UserModel,
    folder_uuid: UUID,
    chat_uuid: UUID,
    detail: str = "Association not found"
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
        .options(selectinload(FolderModel.chat_associations)
                 .selectinload(FolderChatAssociationModel.chat))
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
    folder_type: FolderType | None = FolderType.CUSTOM
) -> FolderModel:
    last_position = await get_last_position(db, user)
    
    folder = FolderModel(
        name=None if folder_info is None else folder_info.name,
        position=last_position + 1,
        user=user,
        folder_type=folder_type
    )
    
    return (await save_to_db(db, [folder]))[0]

async def delete_folder_in_db(
    db: AsyncSession,
    user: UserModel,
    folder: FolderModel
) -> None:
    if folder.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Not your folder'
        )
    
    if folder.folder_type != FolderType.CUSTOM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Only custom folders allowed'
        )
        
    await db.delete(folder)
    await db.commit()
    await reorder_folders_after_deletion(db, user)
    logger.info(f'Folder {folder.name} deleted by {user.username}')

async def add_chat_to_folder(
    db: AsyncSession,
    user: UserModel,
    folder: FolderModel,
    chat: ChatModel
) -> None:
    if not is_user_in_chat(user, chat) or folder.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Chat or folder not accessible'
        )

    if folder.folder_type != FolderType.CUSTOM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Only custom folders allowed'
        )

    try: 
        assoc = FolderChatAssociationModel(folder=folder, chat=chat)
        db.add(assoc)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This chat is already in the folder"
        )

async def delete_chat_from_folder(
    db: AsyncSession,
    assoc: FolderChatAssociationModel
) -> None:
    if assoc.folder.folder_type != FolderType.CUSTOM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Only custom folders allowed'
        )

    await db.delete(assoc)
    await db.commit()

# True - was pinned up | False - was unpinned
async def pin_chat_in_folder(
    db: AsyncSession,
    assoc: FolderChatAssociationModel
) -> bool:
    assoc.is_pinned = not assoc.is_pinned
    await db.commit()

    return assoc.is_pinned
