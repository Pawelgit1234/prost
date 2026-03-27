import { defineStore } from 'pinia'
import axiosInstance from '../api/axios'
import { useAuthStore } from './auth'
import { type ChatI } from './chats'

export const useS3Store = defineStore('s3', {
  state: () => ({}),
  actions: {
    async saveUserAvatar(file: File) {
      const authStore = useAuthStore()
      if (!authStore.currentUser) return

      const formData = new FormData()
      formData.append('file', file)

      const { data } = await axiosInstance.post(
        '/config/user_avatar',
        formData)

      authStore.currentUser.avatar = data.avatar_url
    },
    async saveGroupAvatar(file: File, chat: ChatI) {
      const formData = new FormData()
      formData.append('file', file)

      const { data } = await axiosInstance.post(
        `/config/group_avatar?group_uuid=${chat.uuid}`,
        formData)
      chat.avatar = data.avatar_url
    }
  },
})
