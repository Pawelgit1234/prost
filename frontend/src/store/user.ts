import { defineStore } from 'pinia'
import axiosInstance from '../api/axios'
import { useFolderStore } from './folders'
import { useChatStore } from './chats'
import { useMessageStore } from './messages'

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

export const useUserStore = defineStore('user', {
  state: () => ({
    accessToken: null as string | null, // refreshToken in httponly
    user: null as UserType | null,
  }),
  actions: {
    async logout() {
      await axiosInstance.post('/auth/logout'); // cleans refresh token

      // cleans other data
      this.accessToken = null;
      this.user = null;

      const folderStore = useFolderStore();
      folderStore.$reset();

      const chatStore = useChatStore();
      chatStore.$reset();

      const messageStore = useMessageStore();
      messageStore.$reset();
    }
  },
  persist: true
})
