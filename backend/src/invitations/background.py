from datetime import timedelta
import asyncio
from datetime import datetime
import logging

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.settings import INVITATION_CLEANING_SLEEP_TIME
from src.database import async_session
from src.invitations.models import InvitationModel
from src.invitations.enums import InvitationLifetime

logger = logging.getLogger(__name__)

async def delete_expired_invitations():
    now = datetime.now()

    async with async_session() as session:
        await session.execute(
                delete(InvitationModel).where(
                (
                    (InvitationModel.lifetime == InvitationLifetime.TEN_MINUTES) &
                    (InvitationModel.created_at + timedelta(minutes=10) < now)
                ) |
                (
                    (InvitationModel.lifetime == InvitationLifetime.ONE_HOUR) &
                    (InvitationModel.created_at + timedelta(hours=1) < now)
                ) |
                (
                    (InvitationModel.lifetime == InvitationLifetime.ONE_DAY) &
                    (InvitationModel.created_at + timedelta(days=1) < now)
                )
            )
        )

        await session.commit()

async def periodic_invitation_cleaner():
    while True:
        try:
            await delete_expired_invitations()
            logger.info('Old invitations deleted')
        except Exception as e:
            logger.error(f'Failed to clean invitations: {e}')

        await asyncio.sleep(INVITATION_CLEANING_SLEEP_TIME)