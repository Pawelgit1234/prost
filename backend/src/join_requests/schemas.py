from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.join_requests.enums import JoinRequestType

class CreateJoinRequestSchema(BaseModel):
    """ Schema for creating a join request to either a user or a group """
    target_uuid: UUID # UUID of User or Group
    join_request_type: JoinRequestType # type of join request

class JoinRequestSchema(BaseModel):
    uuid: UUID
    sender_user_uuid: UUID
    sender_username: str
    sender_first_name: str
    sender_last_name: str
    avatar: str | None = Field(default=None)
    
    group_uuid: UUID | None = Field(default=None)

    model_config = ConfigDict(from_attributes=True)
