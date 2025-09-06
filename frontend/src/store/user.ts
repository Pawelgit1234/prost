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
    currentUser: null as UserType | null,
    otherUsers: [] as UserType[] | null,
  }),
  actions: {
    async logout() {
      await axiosInstance.post('/auth/logout'); // cleans refresh token

      // cleans other data
      this.accessToken = null;
      this.currentUser = null;
      this.otherUsers = [];

      const folderStore = useFolderStore();
      folderStore.$reset();

      const chatStore = useChatStore();
      chatStore.$reset();

      const messageStore = useMessageStore();
      messageStore.$reset();
    },

    async login(emailOrUsername: string, password: string) {
      try {
        const formData = new FormData();
        formData.append("username", emailOrUsername);
        formData.append("password", password);
        
        const headers = {
          Accept: "application/json",
          "Content-Type": "application/x-www-form-urlencoded",
        }

        const response = await axiosInstance.post("auth/token", formData, { headers: headers });
        let data = response.data; // { user, access_token, token_type } 

        this.accessToken = data.access_token;
        this.currentUser = data.user as UserType;
      } catch (error) {
        console.log("Error during Login: ", error);
        throw error;
      }
    },

    async register(
      firstName: string,
      lastName: string,
      description: string | null,
      username: string,
      email: string,
      password: string,
    ) {
      try {
        const payload = {
          first_name: firstName,
          last_name: lastName,
          description: description,
          username: username,
          email: email,
          password: password,
        };

        const response = await axiosInstance.post("/auth/register", payload, {
          headers: { "Accept": "application/json" }
        });
        let data = response.data; // { user, access_token, token_type } 

        this.accessToken = data.access_token;
        this.currentUser = data.user as UserType;
      } catch (error) {
        console.log("Error during Register: ", error);
        throw error;
      }
    },

    persist: true
  }
})
