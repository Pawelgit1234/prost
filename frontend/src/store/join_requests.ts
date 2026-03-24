import { defineStore } from 'pinia'
import axiosInstance from '../api/axios'
import { useUserStore } from './users'
import { useChatStore } from './chats'
import { useFolderStore } from './folders'

export interface JoinRequestI {
  uuid: string
  sender_user_uuid: string
  sender_username: string
  sender_first_name: string
  sender_last_name: string
  avatar: string | null

  group_uuid: string | null
}

export const useJoinRequestsStore = defineStore('join_requests', {
  state: () => ({
    userjoinRequests: [] as JoinRequestI[],
    groupjoinRequests: [] as JoinRequestI[],
  }),
  actions: {
    getJoinRequestsByGroupUuid(uuid: string) {
      return this.groupjoinRequests.filter(i => i.group_uuid === uuid)
    },
    async fetchUserJoinRequests() {
      try {
        const response = await axiosInstance.get("/join_requests/user")
        const data = response.data // total, items->join requests
        this.userjoinRequests = data.items as JoinRequestI[]
      } catch (error) {
        console.error("Error fetching user join requests:", error)
      }
    },
    async fetchGroupJoinRequests(groupUuid: string) {
      try {
        const response = await axiosInstance.get(`/join_requests/group?group_uuid=${groupUuid}`)
        const data = response.data // total, items->join requests
        this.groupjoinRequests = data.items as JoinRequestI[]
      } catch (error) {
        console.error("Error fetching group join requests:", error)
      }
    },
    async createJoinRequest(targetUuid: string, joinRequestType: string) {
      try {
        const payload = { target_uuid: targetUuid, join_request_type: joinRequestType };
        const response = await axiosInstance.post('/join_requests/', payload, {
          headers: { 'Accept': 'application/json' },
        });

        if (!response.data.success) {
          console.error("Join Request was not created")
          return
        }

      } catch (error) {
        console.error("Error creating join request: ", error)
      }
    },
    async approveJoinRequest(joinRequestUuid: string) {
      try {
        const response = await axiosInstance.delete(`/join_requests/approve?join_request_uuid=${joinRequestUuid}`)

        if (!response.data.success) {
          console.error("Join Request was not approved")
          return
        }

        const userStore = useUserStore()
        const chatStore = useChatStore()
        const folderStore = useFolderStore()

        this.groupjoinRequests = this.groupjoinRequests.filter(i => i.uuid !== joinRequestUuid)
        this.userjoinRequests = this.userjoinRequests.filter(i => i.uuid !== joinRequestUuid)

        await Promise.all([
          userStore.fetchUsers(),
          chatStore.fetchChats(),
          folderStore.fetchFolders(),
        ])
      } catch (error) {
        console.error("Error approving join request:", error)
      }
    },
    async rejectJoinRequest(joinRequestUuid: string) {
      try {
        const response = await axiosInstance.delete(`/join_requests/reject?join_request_uuid=${joinRequestUuid}`)

        if (!response.data.success) {
          console.error("Join Request was not rejected")
          return
        }

        this.groupjoinRequests = this.groupjoinRequests.filter(i => i.uuid !== joinRequestUuid)
        this.userjoinRequests = this.userjoinRequests.filter(i => i.uuid !== joinRequestUuid)
      } catch (error) {
        console.error("Error rejecting join request:", error)
      }
    },
  },
  persist: true
})
