from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, model_validator, ConfigDict

from src.chats.enums import ChatType
from src.messages.schemas import MessageSchema

class CreateChatSchema(BaseModel):
    chat_type: ChatType # says what type of chat it is: group or normal chat
    name: str = Field(max_length=100)  # group name or username
    group_description: str | None = Field(default=None, max_length=100)  # optional and only for groups

    @model_validator(mode='after')
    def validate_group_or_chat(self) -> 'CreateChatSchema':
        """ Normal chats cannot have a group description """
        if self.chat_type == ChatType.NORMAL and self.group_description is not None:
            raise ValueError("Normal chats cannot have a group description")
        return self

class ChatSchema(BaseModel):
    uuid: UUID
    chat_type: ChatType
    name: str
    description: str
    avatar: str | None = Field(default=None) # optional
    is_open_for_messages: bool
    is_visible: bool
    created_at: datetime
    updated_at: datetime
    last_message: MessageSchema | None = Field(default=None) # optional

    model_config = ConfigDict(from_attributes=True)
