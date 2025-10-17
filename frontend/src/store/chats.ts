import { defineStore } from 'pinia'
import axiosInstance from '../api/axios'

export type ChatType = 'NORMAL' | 'GROUP'

export interface ChatI {
  uuid: string
  chat_type: ChatType
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
  actions: {
    addChat(chat: ChatI) {
      this.chats.push(chat)
    },
    selectChat(uuid: string) {
      this.selectedChatUuid = uuid
    },
    getChatsByFolder() {

    },
    async fetchChats() {
      try {
        const response = await axiosInstance.get("/chats");
        const data = response.data; // total, items->folders
        this.chats = data.items as ChatI[];
      } catch (error) {
        console.log("Error during fetching all chats: ", error);
      }
    }
  },
  persist: true
})
