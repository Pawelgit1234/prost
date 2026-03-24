import { defineStore } from 'pinia'
import axiosInstance from '../api/axios'
import { useFolderStore } from './folders'
import { useChatStore } from './chats'
import { useMessageStore } from './messages'
import { useUserStore } from './users'
import { useInvitationStore } from './invitations'
import { useJoinRequestsStore } from './join_requests'
import { useSearchStore } from './search'
import { useWebSocketStore } from './websocket'

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

export interface UserConfigI {
  first_name: string
  last_name: string
  username: string
  description: string | null
  is_visible: boolean,
  is_open_for_messages: boolean,
  avatar_url: string | null,
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: null as string | null, // refreshToken in httponly
    isLoggedIn: false, // True -> Login, Register, GoogleCallback unaviable | False -> Messenger unaviable
    currentUser: null as UserI | null,
  }),
  actions: {
    async restoreSession() {
     try {
        const response = await axiosInstance.post(
          '/auth/refresh/',
          {},
          { withCredentials: true }
        )

        let data = response.data; // { user, access_token, token_type } 

        this.accessToken = data.access_token;
        this.currentUser = data.user as UserI;
        this.isLoggedIn = true;

        return true
      } catch (e) {
        this.isLoggedIn = false
        return false
      }
    },
    async logout() {
      await axiosInstance.post('/auth/logout', {}, {withCredentials: true}); // cleans refresh token

      // cleans other data
      this.accessToken = null;
      this.currentUser = null;
      this.isLoggedIn = false;

      const folderStore = useFolderStore()
      const chatStore = useChatStore()
      const messageStore = useMessageStore()
      const userStore = useUserStore()
      const invitationStore = useInvitationStore()
      const joinRequestStore = useJoinRequestsStore()
      const searchStore = useSearchStore()
      const websocketStore = useWebSocketStore()

      folderStore.$reset();
      chatStore.$reset();
      messageStore.$reset();
      userStore.$reset();
      invitationStore.$reset();
      joinRequestStore.$reset();
      searchStore.$reset();
      websocketStore.$reset();
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
    },
    async saveConfig(config: UserConfigI) {
      try {
        const response = await axiosInstance.put('/config/user', config, {
          headers: { 'Accept': 'application/json' },
        });

        if (!response.data.success) {
          console.error("Config could not be setted")
          return
        }

        if (this.currentUser) {
          this.currentUser.first_name = config.first_name
          this.currentUser.last_name = config.last_name
          this.currentUser.username = config.username
          this.currentUser.description = config.description
          this.currentUser.is_visible = config.is_visible
          this.currentUser.is_open_for_messages = config.is_open_for_messages
          this.currentUser.avatar = config.avatar_url
        }
      } catch (error) {
        console.error("Error setting user config: ", error)
      }
    },
  },
  persist: {
    pick: ['currentUser', 'isLoggedIn'] // access_token only in memory
  },
})
