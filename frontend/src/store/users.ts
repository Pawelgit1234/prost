import { defineStore } from "pinia";
import type { UserI } from "./auth";

export const useUserStore = defineStore('users', {
  state: () => ({
    users: [] as UserI[] | null,
  }),
  actions: {

  },
  persist: true,
})