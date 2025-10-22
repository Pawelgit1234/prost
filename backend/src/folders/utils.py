from src.folders.models import FolderModel
from src.folders.schemas import FolderSchema

def folder_model_to_schema(folder: FolderModel) -> FolderSchema:
    """Convert SQLAlchemy FolderModel to Pydantic FolderSchema safely."""
    pinned_chats = []
    chat_uuids = []

    for assoc in folder.chat_associations:
        if assoc.chat and assoc.chat.uuid:
            chat_uuids.append(assoc.chat.uuid)
            if assoc.is_pinned:
                pinned_chats.append(assoc.chat.uuid)

    return FolderSchema(
        uuid=folder.uuid,
        name=folder.name,
        folder_type=folder.folder_type,
        position=folder.position,
        pinned_chats=pinned_chats,
        chat_uuids=chat_uuids,
    )
