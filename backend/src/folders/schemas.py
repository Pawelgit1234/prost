from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from src.folders.enums import FolderType

class CreateFolderSchema(BaseModel):
    name: str = Field(max_length=16)

class FolderSchema(BaseModel):
    uuid: UUID
    name: str | None = Field(default=None, max_length=16)
    folder_type: FolderType
    position: int

    pinned_chats: list[UUID]
    chat_uuids: list[UUID]

    model_config = ConfigDict(from_attributes=True)
