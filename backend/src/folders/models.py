from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import String

from src.database import Base
from src.models import TimestampMixin

class Folder(Base, TimestampMixin):
    __tablename__ = 'folders'

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column()

    name: Mapped[str] = mapped_column(String(32))
