from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class ReceiveMessageSchema(BaseModel):
    type: str 
    user_uuid: UUID
    chat_uuid: UUID
    content: str = Field(max_length=5000)

class SendMessageSchema(BaseModel):
    message_uuid: UUID
    user_uuid: UUID # sender
    chat_uuid: UUID
    content: str
    created_at: datetime
    updated_at: datetime # if created_at == updated_at it was not updated

class MessageReadSchema(BaseModel):
    type: str 
    message_uuid: UUID
    chat_uuid: UUID
    
class JoinChatSchema(BaseModel):
    type: str 
    chat_uuid: UUID

class ReadStatusSchema(BaseModel):
    updated_at: datetime
    is_read: bool
    user_uuid: UUID

class MessageSchema(SendMessageSchema):
    read_statuses: list[ReadStatusSchema]