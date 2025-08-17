export interface Folder {
  uuid: string
  name: string
  pos: number
}

export interface Chat {
  uuid: string
  name: string
  folderUuid: string
  lastMessage?: string
  is_pinned: boolean
}

export interface Message {
  uuid: string
  text: string
  author: string
  datetime: string
  isMine: boolean
  wasUpdated: boolean
  chatUuid: string
}