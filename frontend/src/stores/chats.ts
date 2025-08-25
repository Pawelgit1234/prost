import { defineStore } from 'pinia'

export interface ChatType {
  uuid: string
  name: string
  folderUuids: string[]
  lastMessage?: string
  is_pinned: boolean
}

export const useChatStore = defineStore('chats', {
  state: () => ({
    chats: [] as ChatType[],
    selectedChatUuid: '' as string
  }),
  actions: {
    addChat(chat: ChatType) {
      this.chats.push(chat)
    },
    selectChat(uuid: string) {
      this.selectedChatUuid = uuid
    },
    getChatsByFolder(folderUuid: string): ChatType[] {
      return this.chats.filter(c => c.folderUuids.includes(folderUuid))
    }
  },
  persist: true
})
