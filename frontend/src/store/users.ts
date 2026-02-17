import { defineStore } from "pinia";
import type { UserI } from "./auth";
import axiosInstance from "../api/axios";
import { useChatStore } from "./chats";

export const useUserStore = defineStore('users', {
  state: () => ({
    users: [] as UserI[] | null,
  }),
  actions: {
    async fetchUsers() {
      try {
        const response = await axiosInstance.get("/auth")
        const data = response.data // total, items->users
        this.users = data.items as UserI[]
      } catch (error) {
        console.error("Error fetching users:", error)
      }
    },
    getChatUsers(chatUuid: string) {
      const chatStore = useChatStore()
      const chat = chatStore.getChatByUuid(chatUuid)
      if (!chat) return

      const user_uuids = chat.user_uuids

      return this.users?.filter(u => user_uuids.includes(u.uuid))
    },
    getUserFromOneOfTheMembers(memberUuids: string[]) {
      const user = this.users?.find(user => memberUuids.includes(user.uuid))
      return user || null
    }
  },
  persist: true,
})