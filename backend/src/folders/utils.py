from src.folders.models import FolderModel
from src.folders.schemas import FolderSchema

def folder_model_to_schema(folder: FolderModel) -> FolderSchema:
    chat_uuids = [assoc.chat.uuid for assoc in folder.chat_associations]
    pinned_chats = [assoc.chat.uuid for assoc in folder.chat_associations if assoc.is_pinned]

    return FolderSchema(
        uuid=folder.uuid,
        folder_type=folder.folder_type,
        name=folder.name,
        position=folder.position,
        chat_uuids=chat_uuids,
        pinned_chats=pinned_chats
    )
