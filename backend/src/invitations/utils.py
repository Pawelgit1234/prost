from datetime import timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.utils import get_object_or_404
from src.chats.models import ChatModel
from src.invitations.models import InvitationModel
from src.invitations.schemas import InvitationSchema
from src.invitations.enums import InvitationLifetime

def convert_invitation_type_to_datetime(lifetime: InvitationLifetime) -> timedelta | None:
    convertation_dict = {
        InvitationLifetime.TEN_MINUTES: timedelta(minutes=10),
        InvitationLifetime.ONE_HOUR: timedelta(hours=1),
        InvitationLifetime.ONE_DAY: timedelta(days=1),
        InvitationLifetime.UNLIMITED: None,
    }
    return convertation_dict[lifetime]

async def get_invitation_or_404(db: AsyncSession, invitation_uuid: UUID) -> InvitationModel:
    return await get_object_or_404(
        db, InvitationModel, InvitationModel.uuid == invitation_uuid,
        detail='Invitation not found',
        options=[
            selectinload(InvitationModel.user),
            selectinload(InvitationModel.group).selectinload(ChatModel.user_associations)
        ]
    )

def invitation_model_to_schema(
    invitation: InvitationModel,
    group_uuid: UUID | None = None
) -> InvitationSchema:
    if group_uuid is None and invitation.group_id is not None:
            group_uuid = invitation.group.uuid
        
    return InvitationSchema(
        invitation_type=invitation.invitation_type,
        lifetime=invitation.lifetime,
        max_uses=invitation.max_uses,
        uuid=invitation.uuid,
        group_uuid=group_uuid
    )