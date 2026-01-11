import { defineStore } from "pinia";
import type { UserI } from "./auth";
import axiosInstance from "../api/axios";

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
    getUserFromOneOfTheMembers(memberUuids: string[]) {
      const user = this.users?.find(user => memberUuids.includes(user.uuid))
      return user || null
    }
  },
  persist: true,
})