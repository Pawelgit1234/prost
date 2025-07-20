from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.join_requests.enums import JoinRequestType

class CreateJoinRequestSchema(BaseModel):
    """ Schema for creating a join request to either a user or a group """
    target_uuid: UUID # UUID of User or Group
    join_request_type: JoinRequestType # type of join request

class JoinRequestSchema(CreateJoinRequestSchema):
    uuid: UUID
    sender_user_uuid: UUID

    model_config = ConfigDict(from_attributes=True)
