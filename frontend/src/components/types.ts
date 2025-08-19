export interface FolderType {
  uuid: string
  name: string
  pos: number
}

export interface ChatType {
  uuid: string
  name: string
  folderUuid: string
  lastMessage?: string
  is_pinned: boolean
}

export interface MessageType {
  uuid: string
  text: string
  author: string
  datetime: string
  isMine: boolean
  wasUpdated: boolean
  chatUuid: string
}