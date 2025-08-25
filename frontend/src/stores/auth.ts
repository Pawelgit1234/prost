import { defineStore } from 'pinia'

export interface UserType {
  first_name: string
  last_name: string
  username: string
  description: string | null
  email: string
  avatar: string | null
  is_active: boolean
  is_visible: boolean
  is_open_for_messages: boolean
  uuid: string
  created_at: string 
  updated_at: string
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: null as string | null, // refreshToken in HttpOnly
    user: null as UserType | null,
  }),
  actions: {
    setToken(access: string) {
      this.accessToken = access
    },
    setUser(user: UserType) {
      this.user = user
    },
    logout() {
      this.accessToken = null
      this.user = null
    }
  },
  persist: true
})
