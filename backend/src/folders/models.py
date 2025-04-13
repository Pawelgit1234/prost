from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import String

from src.database import BaseModel

class Folder(BaseModel):
    __tablename__ = 'folders'