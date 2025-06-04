from pydantic import BaseModel, Field

class CreateFolderSchema(BaseModel):
    name: str = Field(max_length=16)