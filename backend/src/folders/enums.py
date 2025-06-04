import enum

class FolderType(enum.Enum):
    CUSTOM = 'custom'

    # predefined
    ALL = 'all'
    CHATS = 'chats'
    GROUPS = 'groups'
    NEW = 'new'
