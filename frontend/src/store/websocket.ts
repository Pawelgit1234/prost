import { defineStore } from 'pinia'
import { useMessageStore } from './messages'
import { useAuthStore } from './auth'
import { useFolderStore } from './folders'
import { useChatStore } from './chats'

export const useWebSocketStore = defineStore('ws', {
  state: () => ({
    socket: null as WebSocket | null,
    connected: false
  }),

  actions: {
    connect() {
      if (this.socket) return

      const token = useAuthStore().accessToken
      this.socket = new WebSocket(`${import.meta.env.VITE_WS_ENDPOINT}?token=${token}`)

      this.socket.onopen = () => {
        this.connected = true
        console.log("WS connected")
      }

      this.socket.onclose = () => {
        this.connected = false
        this.socket = null

        setTimeout(() => this.connect(), 2000)
      }

      this.socket.onerror = (e) => {
        console.error("WS error", e)
      }

      this.socket.onmessage = (event) => {
        this.handleMessage(event.data)
      }
    },
    handleMessage(raw: string) {
      const data = JSON.parse(raw)
      const messageStore = useMessageStore()
      const folderStore = useFolderStore()
      const chatStorage = useChatStore()
      const authStorage = useAuthStore()

      switch (data.type) {

        case "new_message":
          messageStore.addMessage(data)
          chatStorage.changeLastMessage(data.chat_uuid, data.content)

          if (data.user_uuid !== authStorage.currentUser?.uuid) {
            this.readMessage(data.chat_uuid)
            folderStore.addChatByFolderByType("new", data.chat_uuid)
          }
          break

        case "read_message":
          messageStore.readMessage(data)
          folderStore.removeChatFromFolderByType("new", data.chat_uuid)
          break

        default:
          console.warn("Unknown WS message", data)
      }
    },
    send(data: any) {
      if (!this.socket || !this.connected) return
      this.socket.send(JSON.stringify(data))
    },
    sendMessage(chatUuid: string, userUuid: string, content: string) {
      this.send({
        type: "new_message",
        user_uuid: userUuid,
        chat_uuid: chatUuid,
        content
      })
    },
    readMessage(chatUuid: string) {
      this.send({
        type: "read_message",
        chat_uuid: chatUuid,
      })
    },
    joinChat(chatUuid: string) {
      this.send({
        type: "join_chat",
        chat_uuid: chatUuid,
      })
    },
    quitChat(chatUuid: string) {
      this.send({
        type: "quit_chat",
        chat_uuid: chatUuid,
      })
    },
  }
})
