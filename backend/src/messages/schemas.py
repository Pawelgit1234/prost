from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.messages.enums import MessageType

class MessageSchema(BaseModel):
    uuid: UUID
    message_type: MessageType
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)