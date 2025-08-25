import { defineStore } from 'pinia'

export interface MessageType {
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
    messages: [] as MessageType[]
  }),
  actions: {
    addMessage(msg: MessageType) {
      this.messages.push(msg)
    },
    updateMessage(uuid: string, text: string) {
      const msg = this.messages.find(m => m.uuid === uuid)
      if (msg) {
        msg.text = text
        msg.wasUpdated = true
      }
    },
    getMessagesByChat(chatUuid: string): MessageType[] {
      return this.messages.filter(m => m.chatUuid === chatUuid)
    }
  },
  persist: true
})
