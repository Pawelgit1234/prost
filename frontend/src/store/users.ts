import { defineStore } from "pinia";
import type { UserType } from "./auth";

export const useUserStore = defineStore('users', {
  state: () => ({
    users: [] as UserType[] | null,
  }),
  actions: {

  },
  persist: true,
})