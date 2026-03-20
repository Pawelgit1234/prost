import { defineStore } from 'pinia'
import axiosInstance from '../api/axios'
import { useAuthStore } from './auth'
import { useChatStore, type ChatI } from './chats'

export const useS3Store = defineStore('s3', {
  state: () => ({}),
  actions: {
    async saveAvatar(file: File) {
        
      const formData = new FormData()
      formData.append('file', file)

      const { data } = await axiosInstance.post(
        '/config/avatar',
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' }
        }
      )
      return data.avatar_url
    },
    async saveUserAvatar(file: File) {
      const authStore = useAuthStore()
      if (!authStore.currentUser) return

      const avatar_url = await this.saveAvatar(file)

      authStore.currentUser.avatar = avatar_url
    },
    async saveGroupAvatar(file: File, chat: ChatI) {
      const avatar_url = await this.saveAvatar(file)
      chat.avatar = avatar_url
    }
  },
})
