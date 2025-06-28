from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from src.database import Base
from src.models import TimestampMixin, uuid_type
from src.messages.enums import MessageType

if TYPE_CHECKING:
    from src.auth.models import UserModel
    from src.chats.models import ChatModel

class MessageModel(Base, TimestampMixin):
    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[uuid_type]

    message_type: Mapped[MessageType]

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["UserModel"] = relationship(back_populates="messages")
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"))
    chat: Mapped["ChatModel"] = relationship(back_populates="messages")
