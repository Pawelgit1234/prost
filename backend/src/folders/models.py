from uuid import UUID
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey

from src.database import Base
from src.models import TimestampMixin

if TYPE_CHECKING:
    from src.auth.models import UserModel
    from src.chats.models import ChatModel

class FolderModel(Base, TimestampMixin):
    __tablename__ = 'folders'

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column()

    name: Mapped[str] = mapped_column(String(32))

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    user: Mapped['UserModel'] = relationship(back_populates='folders')
    chats: Mapped[list['ChatModel']] = relationship(back_populates='folder')
