import enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

from src.database import BaseModel

# Enums

class ChatType(enum.Enum):
    NORMAL = 'normal'
    GROUP = 'group'

class MessageType(enum.Enum):
    TEXT = 'text'
    FILE = 'file'
    BOTH = 'both'

# Models

class UserModel(BaseModel):
    __tablename__ = 'users'

    username: Mapped[str] = mapped_column(String(36))
    password: Mapped[str] = mapped_column()
    email: Mapped[email] = mapped_column()
    first_name: Mapped[str] = mapped_column()
    last_name: Mapped[str] = mapped_column()
    avatar: Mapped[str] = mapped_column() # url
    is_active: Mapped[bool] = mapped_column(default=False)

class ChatModel(Base):
    __tablename__ = 'chats'

class MessageModel(Base):
    __tablename__ = 'messages'
    
class ReadStatusModel(Base):
    __tablename__ = 'read_status'
