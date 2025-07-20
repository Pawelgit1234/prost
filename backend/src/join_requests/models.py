from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, CheckConstraint

from src.database import Base
from src.models import TimestampMixin, uuid_type
from src.join_requests.enums import JoinRequestType

if TYPE_CHECKING:
    from src.auth.models import UserModel
    from src.chats.models import ChatModel

class JoinRequestModel(Base, TimestampMixin):
    """ A request made by a user to join a group or connect with another user """
    __tablename__ = 'join_requests'

    __table_args__ = (
        CheckConstraint(
            'chat_id IS NOT NULL OR receiver_user_id IS NOT NULL',
            name='check_invitation_has_target'
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[uuid_type]

    join_request_type: Mapped[JoinRequestType]

    # Use who sends a request
    sender_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    sender_user: Mapped["UserModel"] = relationship(back_populates="sent_join_requests", foreign_keys=[sender_user_id])
    # Group or a User receives it
    group_id: Mapped[int] = mapped_column(ForeignKey("chats.id"), nullable=True)
    group: Mapped["ChatModel"] = relationship(back_populates="join_requests")
    receiver_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    receiver_user: Mapped["UserModel"] = relationship(back_populates="received_join_requests", foreign_keys=[receiver_user_id])
