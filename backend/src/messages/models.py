from typing import TYPE_CHECKING
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, DateTime, func

from src.database import Base
from src.models import TimestampMixin, uuid_type

if TYPE_CHECKING:
    from src.auth.models import UserModel
    from src.chats.models import ChatModel

class MessageModel(Base, TimestampMixin):
    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[uuid_type]

    content: Mapped[str] = mapped_column(String(5000))

    read_statuses: Mapped[list["ReadStatusModel"]] = relationship(back_populates="message")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["UserModel"] = relationship(back_populates="messages")
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"))
    chat: Mapped["ChatModel"] = relationship(back_populates="messages")

class ReadStatusModel(Base):
    __tablename__ = 'read_statuses'

    id: Mapped[int] = mapped_column(primary_key=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    is_read: Mapped[bool] = mapped_column(default=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["UserModel"] = relationship(back_populates="read_statuses")
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"))
    message: Mapped[MessageModel] = relationship(back_populates="read_statuses")
    