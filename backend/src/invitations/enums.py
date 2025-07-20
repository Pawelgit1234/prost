from enum import Enum

class InvitationLifetime(Enum):
    TEN_MINUTES = '10m'
    ONE_HOUR = '1h'
    ONE_DAY = '1d'
    UNLIMITED = 'unlimited'