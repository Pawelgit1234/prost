from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey

from src.database import Base
from src.models import TimestampMixin, uuid_type
from src.folders.enums import FolderType

if TYPE_CHECKING:
    from src.auth.models import UserModel
    from src.chats.models import ChatModel

class FolderChatAssociationModel(Base):
    __tablename__ = 'folder_chat_associations'

    # relationships
    folder: Mapped['FolderModel'] = relationship(back_populates='chat_associations')
    folder_id: Mapped[int] = mapped_column(ForeignKey('folders.id'), primary_key=True)
    chat: Mapped['ChatModel'] = relationship(back_populates='folder_associations')
    chat_id: Mapped[int] = mapped_column(ForeignKey('chats.id'), primary_key=True)

class FolderModel(Base, TimestampMixin):
    __tablename__ = 'folders'

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[uuid_type]

    folder_type: Mapped[FolderType]
    name: Mapped[str] = mapped_column(String(16))
    position: Mapped[int] = mapped_column(default=0) # folder ordering

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    user: Mapped['UserModel'] = relationship(back_populates='folders')
    chat_associations: Mapped[list["FolderChatAssociationModel"]] = relationship(
        back_populates='folder', cascade='all, delete-orphan'
    )
