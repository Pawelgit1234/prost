from uuid import UUID
import asyncio

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from sqlalchemy.orm import selectinload

from src.utils import save_to_db, get_object_or_404
from src.auth.models import UserModel
from src.chats.models import ChatModel
from src.chats.schemas import ChatSchema
from src.folders.models import FolderModel, FolderChatAssociationModel
from src.folders.schemas import CreateFolderSchema
from src.folders.enums import FolderType

async def get_all_folders(db: AsyncSession, user: UserModel) -> list[FolderModel]:
    result = await db.execute(
        select(FolderModel)
        .where(FolderModel.user_id == user.id)
        .order_by(FolderModel.position)
    )
    return await result.all()

async def get_all_chats_from_folder(
    db: AsyncSession, 
    folder_uuid: UUID
) -> list[ChatSchema]:
    folder = await get_object_or_404(
        db, FolderModel, FolderModel.uuid == folder_uuid,
        options=[selectinload(FolderModel.chat_associations)],
        detail='Folder not found'
    )

    result = await db.execute(
        select(ChatModel, FolderChatAssociationModel.is_pinned)
        .join(FolderChatAssociationModel, ChatModel.id == FolderChatAssociationModel.chat_id)
        .where(FolderChatAssociationModel.folder_id == folder.id)
    )

    chats_with_pins = result.all()

    chat_schemas: list[ChatSchema] = []
    for chat, is_pinned in chats_with_pins:
        chat_data = {
            **chat.__dict__,
            "is_pinned": is_pinned
        }
        chat_schema = ChatSchema.model_validate(chat_data)
        chat_schemas.append(chat_schema)

    return chat_schemas

async def get_last_position(db: AsyncSession, user: UserModel) -> int:
    result = await db.execute(
        select(FolderModel.position)
        .where(FolderModel.user_id == user.id)
        .order_by(desc(FolderModel.position))
        .limit(1)
    )
    return result.scalar_one_or_none() or -1

async def reorder_folders_after_deletion(db: AsyncSession, user: UserModel) -> None:
    result = await db.execute(
        select(FolderModel)
        .where(FolderModel.user_id == user.id)
        .order_by(FolderModel.position)
    )
    folders = result.all()

    if folders is not None:
        for new_pos, folder in enumerate(folders):
            folder.position = new_pos
        await db.commit()

async def create_folder_in_db(
    db: AsyncSession,
    user: UserModel,
    folder_info: CreateFolderSchema | None = None,
    folder_type: FolderType | None = FolderType.CUSTOM
) -> FolderModel:
    last_position = await get_last_position()
    
    folder = FolderModel(
        name=None if folder_info is None else folder_info.name, position=last_position + 1,
        user=user, folder_type=folder_type
    )
    
    return (await save_to_db(db, [folder]))[0]

async def delete_folder_in_db(
    db: AsyncSession,
    user: UserModel,
    folder_uuid: UUID
) -> None:
    folder = await get_object_or_404(
        db, FolderModel, FolderModel.uuid == folder_uuid,
        detail='Folder not found'
    )

    if folder.user.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You can delete only your folders'
        )
    
    if folder.folder_type == FolderType.CUSTOM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You can delete only custom folders'
        )
        
    await db.delete(folder)
    await db.commit()

async def add_chat_to_folder(
    db: AsyncSession,
    user: UserModel,
    folder_uuid: UUID,
    chat_uuid: UUID
) -> ChatModel:
    # two requests 'parallel' are faster
    folder, chat = await asyncio.gather(
        get_object_or_404(db, FolderModel, FolderModel.uuid == folder_uuid, detail='Folder not found'),
        get_object_or_404(db, ChatModel, ChatModel.uuid == chat_uuid, detail='Chat not found')
    )

    if user not in chat.user_associations or folder.user.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You can add chats to folders which belongs to you'
        )

    assoc = FolderChatAssociationModel(folder=folder, chat=chat)

    if folder.folder_type == FolderType.CUSTOM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You can add chats only to custom folders'
        )
    
    await save_to_db(db, [assoc])
    return chat

async def delete_chat_from_folder(
    db: AsyncSession,
    user: UserModel,
    folder_uuid: UUID,
    chat_uuid: UUID
) -> None:
    result = await db.execute(
        select(FolderChatAssociationModel)
        .join(FolderModel, FolderChatAssociationModel.folder_id == FolderModel.id)
        .join(ChatModel, FolderChatAssociationModel.chat_id == ChatModel.id)
        .where(
            and_(
                FolderModel.uuid == folder_uuid,
                FolderModel.user_id == user.id,
                ChatModel.uuid == chat_uuid
            )
        )
    )
    assoc = result.scalar_one_or_none()
    
    if assoc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Association not found')

    if assoc.folder.folder_type == FolderType.CUSTOM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You can delete chats only to custom folders'
        )

    await db.delete(assoc)
    await db.commit()

# False - was unpinned
# True - was pinned up
async def pin_chat_in_folder(
    db: AsyncSession,
    user: UserModel,
    folder_uuid: UUID,
    chat_uuid: UUID
) -> bool:
    result = await db.execute(
        select(FolderChatAssociationModel)
        .join(FolderModel, FolderChatAssociationModel.folder_id == FolderModel.id)
        .join(ChatModel, FolderChatAssociationModel.chat_id == ChatModel.id)
        .where(
            and_(
                FolderModel.uuid == folder_uuid,
                ChatModel.uuid == chat_uuid
            )
        )
    )
    assoc = result.scalar_one_or_none()
    
    if assoc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Association not found')

    assoc.is_pinned = not assoc.is_pinned
    await db.commit()

    return assoc.is_pinned
