from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from src.folders.enums import FolderType

class CreateFolderSchema(BaseModel):
    name: str | None = Field(default=None, max_length=16)

class FolderSchema(CreateFolderSchema):
    uuid: UUID
    folder_type: FolderType

    model_config = ConfigDict(from_attributes=True)
