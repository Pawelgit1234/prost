from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from src.folders.enums import FolderType

class CreateFolderSchema(BaseModel):
    name: str = Field(max_length=16)

class ReplaceChatsSchema(BaseModel):
    uuids: list[UUID] # chat uuids

class FolderSchema(BaseModel):
    uuid: UUID
    name: str | None = Field(default=None)
    folder_type: FolderType
    position: int

    pinned_chats: list[UUID] | None = Field(default=None)
    chat_uuids: list[UUID] | None = Field(default=None)

    # created_at & updated_at are unimportant here

    model_config = ConfigDict(from_attributes=True)
