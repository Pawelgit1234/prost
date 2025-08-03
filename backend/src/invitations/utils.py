from datetime import datetime

from src.invitations.enums import InvitationLifetime

def convert_invitation_type_to_datetime(lifetime: InvitationLifetime) -> datetime | None:
    convertation_dict = {
        InvitationLifetime.TEN_MINUTES: datetime.minute(10),
        InvitationLifetime.ONE_HOUR: datetime.hour(1),
        InvitationLifetime.ONE_DAY: datetime.day(1),
        InvitationLifetime.UNLIMITED: None,
    }
    return convertation_dict[lifetime]