from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from src.database import Base
from src.models import TimestampMixin, uuid_type

if TYPE_CHECKING:
    from src.auth.models import UserModel
    from src.chats.models import ChatModel

class JoinRequestModel(Base, TimestampMixin):
    __tablename__ = 'join_requests'

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[uuid_type]
