import { defineStore } from 'pinia'

export interface MessageI {
  uuid: string
  text: string
  author: string
  datetime: string
  isMine: boolean
  wasUpdated: boolean
  chatUuid: string
}

export const useMessageStore = defineStore('messages', {
  state: () => ({
    messages: [] as MessageI[]
  }),
  actions: {
    addMessage(msg: MessageI) {
      this.messages.push(msg)
    },
    updateMessage(uuid: string, text: string) {
      const msg = this.messages.find(m => m.uuid === uuid)
      if (msg) {
        msg.text = text
        msg.wasUpdated = true
      }
    },
    getMessagesByChat(chatUuid: string): MessageI[] {
      return this.messages.filter(m => m.chatUuid === chatUuid)
    },
    async deleteChatMessages(chatUuid: string) {
      // TODO: delete all chat message
    }
  },
  persist: true
})
