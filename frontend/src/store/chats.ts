import { defineStore } from 'pinia'
import axiosInstance from '../api/axios'
import { useFolderStore, type FolderI } from './folders'
import { useAuthStore } from './auth';
import { useUserStore } from './users';
import { useWebSocketStore } from './websocket';

export interface ChatI {
  uuid: string
  chat_type: 'group' | 'normal';
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
    getChatByUuid(uuid: string) {
      return this.chats.find(c => c.uuid == uuid)
    },
    getChatsByFolder(folder?: FolderI) {
      if (!folder) return []
      return this.chats.filter(c => folder.chat_uuids.includes(c.uuid))
    },
    changeLastMessage(chatUuid: string, lastMessage: string) {
      const chat = this.getChatByUuid(chatUuid)
      if (chat) chat.last_message = lastMessage
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

        const websocketStore = useWebSocketStore()
        websocketStore.quitChat(groupUuid)
      } catch (error) {
        console.error("Error quitting group: ", error)
      }

      const userStore = useUserStore()
      await userStore.fetchUsers()
    },
    async deleteChat(chatUuid: string) {
      try {
        const response = await axiosInstance.delete(`/chats/${chatUuid}`)

        if (response.data.success) {
          this.chats = this.chats.filter((chat) => chat.uuid !== chatUuid)
        } else {
          console.error("Chat was not deleted")
        }

        const websocketStore = useWebSocketStore()
        websocketStore.quitChat(chatUuid)
      } catch (error) {
        console.error("Error deleting chat:", error)
      }

      const userStore = useUserStore()
      await userStore.fetchUsers()
    },
    async addUserToGroup(group: ChatI, userUuids: string[]) {
      const authStore = useAuthStore()
      if (authStore.currentUser) {
        userUuids.push(authStore.currentUser?.uuid)
      } else {
        console.error("Current user not found")
        return
      }

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
    },
    async joinGroup(group_uuid: string) {
      const authStore = useAuthStore()
      const userStore = useUserStore()
      const folderStore = useFolderStore()

      if (!authStore.currentUser) {
          console.error("You was not added to group")
          return
      }

      try {
        const response = await axiosInstance.put(`/chats/join_group/${group_uuid}`);
        const group = response.data as ChatI
        this.chats.push(group)

        await userStore.fetchUsers()
        await folderStore.fetchFolders()


        const websocketStore = useWebSocketStore()
        websocketStore.joinChat(group_uuid)
      } catch (error) {
        console.error("Error adding you to group: ", error)
      }
    },
    async createChat(username: string) {
      const authStore = useAuthStore()
      const userStore = useUserStore()
      const folderStore = useFolderStore()

      if (!authStore.currentUser) {
          console.error("Chat was not created")
          return
      }

      try {
        const payload = { chat_type: 'normal', name: username };
        const response = await axiosInstance.post('/chats/', payload, {
          headers: { 'Accept': 'application/json' },
        });
        const chat = response.data as ChatI
        this.chats.push(chat)

        await userStore.fetchUsers()
        await folderStore.fetchFolders()

        const websocketStore = useWebSocketStore()
        websocketStore.joinChat(chat.uuid)

        return chat
      } catch (error) {
        console.error("Error creating chat: ", error)
      }
    }
  },
  persist: true
})
