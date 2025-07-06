from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, model_validator, ConfigDict

from src.chats.enums import ChatType

class CreateChatSchema(BaseModel):
    chat_type: ChatType  # says what type of chat it is: group or normal chat
    name: str = Field(max_length=100)  # group name or username
    group_description: str | None = Field(default=None, max_length=100)  # optional and only for groups

    @model_validator(mode='after')
    def validate_group_or_chat(self) -> 'CreateChatSchema':
        """ Normal chats cannot have a group description """
        if self.chat_type == ChatType.NORMAL and self.group_description is not None:
            raise ValueError("Normal chats cannot have a group description")
        return self

class ChatSchema(CreateChatSchema):
    is_pinned: bool = Field(default=False)
    created_at: datetime
    updated_at: datetime
    uuid: UUID
    avatar: str | None = Field(default=None) # optional

    model_config = ConfigDict(from_attributes=True)
