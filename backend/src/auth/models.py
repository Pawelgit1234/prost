from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

from src.database import Base
from src.models import TimestampMixin, uuid_type
from src.chats.models import ChatModel, MessageModel

class UserModel(Base, TimestampMixin):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[uuid_type]

    first_name: Mapped[str] = mapped_column(String(32))
    last_name: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password: Mapped[str]
    avatar: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=False)
    is_pinned_up: Mapped[bool] = mapped_column(default=False)
