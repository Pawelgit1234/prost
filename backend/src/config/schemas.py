from pydantic import BaseModel, Field

class UserConfigSchema(BaseModel):
    first_name: str = Field(max_length=32)
    last_name: str = Field(max_length=32)
    username: str = Field(max_length=16)
    description: str = Field(max_length=100)
    is_visible: bool
    is_open_for_messages: bool
    avatar_url: str | None = Field(default=None)

class GroupConfigSchema(BaseModel):
    name: str = Field(max_length=100)
    description: str = Field(max_length=100)
    is_open_for_messages: bool
    is_visible: bool
    avatar_url: str | None = Field(default=None)