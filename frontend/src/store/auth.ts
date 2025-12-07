import { defineStore } from 'pinia'
import axiosInstance from '../api/axios'
import { useFolderStore } from './folders'
import { useChatStore } from './chats'
import { useMessageStore } from './messages'
import { useUserStore } from './users'

export interface UserI {
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
    accessToken: null as string | null, // refreshToken in httponly
    isLoggedIn: false, // True -> Login, Register, GoogleCallback unaviable | False -> Messenger unaviable
    currentUser: null as UserI | null,
  }),
  actions: {
    async logout() {
      await axiosInstance.post('/auth/logout'); // cleans refresh token

      // cleans other data
      this.accessToken = null;
      this.currentUser = null;

      const folderStore = useFolderStore();
      folderStore.$reset();

      const chatStore = useChatStore();
      chatStore.$reset();

      const messageStore = useMessageStore();
      messageStore.$reset();

      const userStore = useUserStore();
      userStore.$reset();

      this.isLoggedIn = false;
    },

    async login(emailOrUsername: string, password: string) {
      try {
        const formData = new FormData();
        formData.append("username", emailOrUsername);
        formData.append("password", password);

        const response = await axiosInstance.post("/auth/token", formData, {
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          withCredentials: true, // true, because server sets the refresh token
        });
        let data = response.data; // { user, access_token, token_type } 

        this.accessToken = data.access_token;
        this.currentUser = data.user as UserI;
        this.isLoggedIn = true;
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
          headers: { "Accept": "application/json" },
          withCredentials: true, // true, because server sets the refresh token
        });
        let data = response.data; // { user, access_token, token_type } 

        this.accessToken = data.access_token;
        this.currentUser = data.user as UserI;
        this.isLoggedIn = true;
      } catch (error) {
        console.log("Error during Register: ", error);
        throw error;
      }
    },

    async loginWithGoogle(code: string, state: string) {
      try {
        const response = await axiosInstance.post("/auth/google/callback", {
          code,
          state,
        });
        let data = response.data; // { user, access_token, token_type } 
        this.accessToken = data.access_token;
        this.currentUser = data.user as UserI;
        this.isLoggedIn = true;
      } catch (error) {
        console.log("Error during Login with Google: ", error);
      }
    }
  },
  persist: {
    pick: ['currentUser', 'isLoggedIn'] // access_token only in memory
  },
})
