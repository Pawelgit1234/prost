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
  user_uuids: string[]
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
    async quitChat(groupUuid: string) {
      try {
        const response = await axiosInstance.delete(`/chats/${groupUuid}/quit`)

        if (response.data.success) {
          this.chats = this.chats.filter((chat) => chat.uuid !== groupUuid)
        } else {
          console.error("Group was not quitted")
        }
      } catch (error) {
        console.error("Error quitting group: ", error)
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
    },
    async addUserToGroup(group: ChatI, userUuids: string[]) {
      try {
        const payload = { group_uuid: group.uuid, user_uuids: userUuids };
        const response = await axiosInstance.put('/chats/add_user', payload, {
          headers: { 'Accept': 'application/json' },
        });

        if (!response.data.success) {
          console.error("Users were not added to group")
          return
        }

        group.user_uuids = userUuids

      } catch (error) {
        console.error("Error adding users to group: ", error)
      }
    }
  },
  persist: true
})
