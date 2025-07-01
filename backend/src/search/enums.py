from enum import Enum

class VisibilityLevel(Enum):
    """ Groups and users visibility level """
    PUBLIC = 'public'   # Visible in search; anyone can start a chat with you
    REQUEST = 'request' # Visible in search; chat requests require your approval
    HIDDEN = 'hidden'   # Not visible in search
