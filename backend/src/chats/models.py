from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String

from src.database import Base
from src.models import TimestampMixin, uuid_type
from src.chats.enums import ChatType

if TYPE_CHECKING:
    from src.auth.models import UserModel
    from src.folders.models import FolderModel
    from src.messages.models import MessageModel

class UserChatAssociationModel(Base):
    __tablename__ = 'user_chat_associations'

    # ids
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey('chats.id'), primary_key=True)

    # extra fields
    is_pinned: Mapped[bool] = mapped_column(default=False)

    # relationships
    user: Mapped['UserModel'] = relationship(back_populates='chat_associations')
    chat: Mapped['ChatModel'] = relationship(back_populates='user_associations')

class ChatModel(Base, TimestampMixin):
    __tablename__ = 'chats'

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[uuid_type]

    # for chat and groups
    chat_type: Mapped[ChatType]
    name: Mapped[str] = mapped_column(String(100))
    # for groups
    description: Mapped[str] = mapped_column(String(100), nullable=True)
    avatar: Mapped[str] = mapped_column(nullable=True) # avatar will be set later in settings


    messages: Mapped[list["MessageModel"]] = relationship(back_populates="chat")
    user_associations: Mapped[list["UserChatAssociationModel"]] = relationship(
        back_populates='chat', cascade='all, delete-orphan'
    )
    folder_id: Mapped[int] = mapped_column(ForeignKey('folders.id'), nullable=True)
    folder: Mapped['FolderModel'] = relationship(back_populates='chats')
