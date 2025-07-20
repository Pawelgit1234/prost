from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis

from src.utils import save_to_db, get_object_or_404, get_all_objects
from src.auth.models import UserModel
from src.chats.models import ChatModel
from src.chats.schemas import CreateChatSchema
from src.chats.enums import ChatType
from src.chats.utils import is_user_in_chat, get_common_chats
from src.chats.services import add_user_to_group_in_db, create_chat_in_db
from src.join_requests.models import JoinRequestModel
from src.join_requests.enums import JoinRequestType
from src.join_requests.schemas import CreateJoinRequestSchema

async def get_all_group_join_requests_list(
    db: AsyncSession,
    user: UserModel,
    group: ChatModel
) -> list[JoinRequestModel]:
    if not is_user_in_chat(user, group):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Only group members can get all join requests'
        )

    join_requests = await get_all_objects(
        db, JoinRequestModel, JoinRequestModel.group_id == group.id
    )

    return join_requests

async def create_join_request_in_db(
    db: AsyncSession,
    user: UserModel,
    join_request_info: CreateJoinRequestSchema
) -> JoinRequestModel:
    if join_request_info.join_request_type == JoinRequestType.USER:
        target = await get_object_or_404(
            db, UserModel, UserModel.uuid == join_request_info.target_uuid,
            detail='User not found'
        )

        # checks if user has a normal chat with other user
        common_chats = await get_common_chats(db, user, target)
        chat_types = [chat.chat_type for chat in common_chats]
        
        if ChatType.NORMAL in chat_types:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You already have a normal chat with user'
            )
        
        join_request = JoinRequestModel(
            sender_user=user, receiver_user=target,
            join_request_type=join_request_info.join_request_type
        )
    elif join_request_info.join_request_type == JoinRequestType.GROUP:
        target = await get_object_or_404(
            db, ChatModel, ChatModel.uuid == join_request_info.target_uuid,
            detail='Group not found'
        )

        if is_user_in_chat(user, join_request.group):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You already in the group'
            )

        join_request = JoinRequestModel(
            sender_user=user, group=target,
            join_request_type=join_request_info.join_request_type
        )
    
    if target.is_open_for_messages:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='User is open for messages'
        )
    
    join_request = (await save_to_db(db, [join_request]))[0]

    user.sent_join_requests = join_request
    target.received_join_requests = join_request

    await db.commit()
    return join_request

async def approve_join_request_in_db(
    db: AsyncSession,
    r: Redis,
    user: UserModel,
    join_request: JoinRequestModel,
) -> None:
    if join_request.join_request_type == JoinRequestType.USER:
        if join_request.receiver_user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You are not authorized to approve this join request'
            )

        await create_chat_in_db(db, r, user, CreateChatSchema(
            chat_type=ChatType.NORMAL,
            name=join_request.sender_user.username
        ))
    elif join_request.join_request_type == JoinRequestType.GROUP:
        # already checks if receiver in the group
        await add_user_to_group_in_db(db, r, join_request.group, join_request.sender_user, user)
    
    await db.delete(join_request)
    await db.commit()

async def reject_join_request_in_db(
    db: AsyncSession,
    user: UserModel,
    join_request: JoinRequestModel,
) -> None:
    if join_request.join_request_type == JoinRequestType.USER:
        if join_request.receiver_user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You are not authorized to reject this join request'
            )
    elif join_request.join_request_type == JoinRequestType.GROUP:
        if not is_user_in_chat(user, join_request.group):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Only group members can reject join requests'
            )

    await db.delete(join_request)
    await db.commit()
