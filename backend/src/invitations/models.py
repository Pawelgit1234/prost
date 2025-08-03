from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, CheckConstraint

from src.database import Base
from src.models import TimestampMixin, uuid_type
from src.invitations.enums import InvitationLifetime, InvitationType

if TYPE_CHECKING:
    from src.auth.models import UserModel
    from src.chats.models import ChatModel

class InvitationModel(Base, TimestampMixin):
    """ An invitation created by a user or group, typically shared via an invite link """
    __tablename__ = 'invitations'

    __table_args__ = (
        CheckConstraint(
            'group_id IS NOT NULL OR user_id IS NOT NULL',
            name='check_invitation_has_target'
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[uuid_type]

    invitation_type: Mapped[InvitationType]
    max_uses: Mapped[int] = mapped_column(default=1, nullable=True) # null = unlimited
    lifetime: Mapped[InvitationLifetime]

    # Group or User who creates an invitation
    group_id: Mapped[int] = mapped_column(ForeignKey("chats.id"), nullable=True)
    group: Mapped["ChatModel"] = relationship(back_populates="invitations")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    user: Mapped["UserModel"] = relationship(back_populates="invitations")
