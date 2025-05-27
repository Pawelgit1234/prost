from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, ConfigDict

from src.chats.enums import ChatType

class CreateChatSchema(BaseModel):
    chat_type: ChatType # says what type of chat it is: group or normal chat
    name: str = Field(max_length=100) # group name or username
    group_description: str | None = Field(default=None, max_length=100) # optional

    @field_validator('group_description')
    @classmethod
    def validate_group_or_chat(cls, v, values) -> str:
        if values.get('chat_type') == ChatType.GROUP and not v:
            raise ValueError("Group description is required for group chats")
        return v

class ChatSchema(CreateChatSchema):
    is_pinned: bool
    created_at: datetime
    updated_at: datetime
    uuid: UUID
    avatar: str | None = Field(default=None) # optional

    model_config = ConfigDict(from_attributes=True)
