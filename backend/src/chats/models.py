from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

from src.database import Base
from src.models import TimestampMixin
from src.chats.enums import ChatType, MessageType
from src.auth.models import UserModel

class ChatModel(Base, TimestampMixin):
    __tablename__ = 'chats'

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column()

    chat_type: Mapped[ChatType]

class MessageModel(Base, TimestampMixin):
    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column()

    message_type: Mapped[MessageType]
