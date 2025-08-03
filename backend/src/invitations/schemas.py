from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, model_validator

from src.invitations.enums import InvitationLifetime, InvitationType

class CreateInvitationSchema(BaseModel):
    invitation_type: InvitationType
    lifetime: InvitationLifetime
    max_uses: int | None = Field(default=None, gt=0) # greater than 0 or null

    group_uuid: UUID | None = Field(default=None) # only for groups

    @model_validator(mode='after')
    def validate_group_or_user(self) -> 'CreateInvitationSchema':
        if self.invitation_type == InvitationType.USER and self.group_uuid is not None:
            raise ValueError("User invitation cannot have group_uuid")
        return self

class InvitationSchema(CreateInvitationSchema):
    uuid: UUID # on fronted will be generate link and qr code

    model_config = ConfigDict(from_attributes=True)