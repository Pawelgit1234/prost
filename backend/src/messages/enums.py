import enum

class MessageType(enum.Enum):
    TEXT = 'text'
    FILE = 'file'
    BOTH = 'both'