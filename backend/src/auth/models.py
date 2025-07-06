from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey

from src.database import Base
from src.models import TimestampMixin, uuid_type

if TYPE_CHECKING:
    from src.chats.models import UserChatAssociationModel
    from src.folders.models import FolderModel
    from src.messages.models import MessageModel

class UserModel(Base, TimestampMixin):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[uuid_type]

    first_name: Mapped[str] = mapped_column(String(32))
    last_name: Mapped[str] = mapped_column(String(32))
    username: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(100), nullable=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(60), nullable=True)
    # avatar will be set later in settings
    avatar: Mapped[str] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=False)
    is_visible: Mapped[bool] = mapped_column(default=False) # search

    messages: Mapped[list["MessageModel"]] = relationship(back_populates="user")
    folders: Mapped[list["FolderModel"]] = relationship(back_populates="user")
    email_activation_token: Mapped["EmailActivationTokenModel"] = relationship(
        back_populates="user", uselist=False
    )
    chat_associations: Mapped[list["UserChatAssociationModel"]] = relationship(
        back_populates='user', cascade='all, delete-orphan'
    )

# I do not know why, but without this it just do not work
from src.messages.models import MessageModel
from src.folders.models import FolderModel

class EmailActivationTokenModel(Base, TimestampMixin):
    __tablename__ = 'email_activation_tokens'

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[uuid_type]
    
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=True, unique=True)
    user: Mapped["UserModel"] = relationship(back_populates='email_activation_token')
