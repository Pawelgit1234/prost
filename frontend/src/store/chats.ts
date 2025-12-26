import { defineStore } from 'pinia'
import axiosInstance from '../api/axios'
import { useFolderStore, type FolderI } from './folders'

export interface ChatI {
  uuid: string
  chat_type: string
  name: string
  description: string
  avatar?: string // url
  is_open_for_messages: boolean
  is_visible: boolean
  last_message?: string
  created_at: string
  updated_at: string
}

export const useChatStore = defineStore('chats', {
  state: () => ({
    chats: [] as ChatI[],
    selectedChatUuid: '' as string
  }),
  getters: {
    selectedChat(state) {
      return state.chats.find(c => c.uuid === state.selectedChatUuid)
    },
    chatsOfSelectedFolder(state) {
      const folderStore = useFolderStore()
      const folder = folderStore.folders.find(f => f.uuid === folderStore.selectedFolderUuid)
      if (!folder) return []
      const chatUuids = folder.chat_uuids ?? []
      return state.chats.filter(c => chatUuids.includes(c.uuid))
    }
  },
  actions: {
    selectChat(uuid: string) {
      this.selectedChatUuid = uuid
    },
    addChat(chat: ChatI) {
      this.chats.push(chat)
    },
    getChatsByFolder(folder?: FolderI) {
      if (!folder) return []
      return this.chats.filter(c => folder.chat_uuids.includes(c.uuid))
    },
    async fetchChats() {
      try {
        const response = await axiosInstance.get("/chats")
        const data = response.data // total, items->chats
        this.chats = data.items as ChatI[]
      } catch (error) {
        console.error("Error fetching chats:", error)
      }
    },
    async deleteChat(chatUuid: string) {
      try {
        const response = await axiosInstance.delete(`/chats/${chatUuid}`)

        if (response.data.success) {
          this.chats = this.chats.filter((chat) => chat.uuid !== chatUuid)
        } else {
          console.error("Chat was not deleted")
        }
      } catch (error) {
        console.error("Error deleting chat:", error)
      }
    }
  },
  persist: true
})
