import { defineStore } from 'pinia'
import axiosInstance from '../api/axios'
import { useUserStore } from './users'

export interface MessageReadI {
  type: string,
  chat_uuid: string,
  user_uuid: string,
}

export interface ReadStatusI {
  updated_at: string,
  is_read: boolean,
  user_uuid: string
}

export interface MessageI {
  uuid: string,
  user_uuid: string,
  chat_uuid: string,
  content: string,
  created_at: string,
  updated_at: string,
  read_statuses: ReadStatusI[]
}

export const useMessageStore = defineStore('messages', {
  state: () => ({
    messages: [] as MessageI[]
  }),
  actions: {
    getMessagesByChat(chatUuid: string): MessageI[] {
      return this.messages.filter(m => m.chat_uuid === chatUuid)
    },
    getMessageByUuid(messageUuid: string): MessageI | undefined {
      return this.messages.find(m => m.uuid === messageUuid)
    },
    deleteChatMessages(chatUuid: string) {
      this.messages = this.messages.filter(m => m.chat_uuid === chatUuid);
    },
    addMessage(message: MessageI) {
      this.messages.push(message)

      const userStore = useUserStore()
      const users = userStore.getChatUsers(message.chat_uuid)

      const read_statuses = users?.map(u => ({
        updated_at: message.created_at,
        is_read: false,
        user_uuid: u.uuid
      })) ?? []

      message.read_statuses = read_statuses
    },
    readMessage(read: MessageReadI) {
      for (const m of this.messages) {
        if (m.chat_uuid !== read.chat_uuid) continue

        const status = m.read_statuses.find(
          r => r.user_uuid === read.user_uuid
        )

        if (status) status.is_read = true
      }
    },
    async fetchMessages(chatUuid: string) {
      try {
        const { data } = await axiosInstance.get(`/messages/${chatUuid}`)
        this.messages = [
          ...this.messages.filter(m => m.chat_uuid !== chatUuid),
          ...data.items
        ]
      } catch (error) {
        console.error("Error fetching messages:", error)
      }
    }
  },
  persist: true
})
