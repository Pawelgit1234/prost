import enum

class ChatType(enum.Enum):
    NORMAL = 'normal'
    GROUP = 'group'

class MessageType(enum.Enum):
    TEXT = 'text'
    FILE = 'file'
    BOTH = 'both'