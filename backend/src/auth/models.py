from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String

from src.database import Base
from src.models import TimestampMixin, uuid_type
from src.chats.models import user_chat_association_table

if TYPE_CHECKING:
    from src.chats.models import ChatModel, MessageModel
    from src.folders.models import FolderModel

class UserModel(Base, TimestampMixin):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[uuid_type]

    first_name: Mapped[str] = mapped_column(String(32))
    last_name: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password: Mapped[str]
    avatar: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=False)

    chats: Mapped[list["ChatModel"]] = relationship(
        secondary=user_chat_association_table, back_populates='users'
    )
    messages: Mapped[list["MessageModel"]] = relationship(back_populates="user")
    folders: Mapped[list["FolderModel"]] = relationship(back_populates="user")
