from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Table, Column

from src.database import Base
from src.models import TimestampMixin
from src.chats.enums import ChatType, MessageType
from src.auth.models import UserModel
from src.folders.models import FolderModel

user_chat_association_table = Table(
    'user_chat_association_table',
    Base.metadata,
    Column('user_id', ForeignKey('users.id'), primary_key=True),
    Column('chat_id', ForeignKey('chats.id'), primary_key=True)
)

class ChatModel(Base, TimestampMixin):
    __tablename__ = 'chats'

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column()

    chat_type: Mapped[ChatType]
    is_pinned_up: Mapped[bool] = mapped_column(default=False)

    messages: Mapped[list["MessageModel"]] = relationship(back_populates="chat")
    users: Mapped[list["UserModel"]] = relationship(
        secondary=user_chat_association_table, back_populates='chats'
    )
    folder_id = Mapped[int] = mapped_column(ForeignKey('folders.id'))
    folder: Mapped['FolderModel'] = relationship(back_populates='chats')

class MessageModel(Base, TimestampMixin):
    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column()

    message_type: Mapped[MessageType]

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["UserModel"] = relationship(back_populates="messages")
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"))
    chat: Mapped["ChatModel"] = relationship(back_populates="messages")
