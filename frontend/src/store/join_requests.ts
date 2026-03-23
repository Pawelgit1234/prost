import { defineStore } from 'pinia'
import axiosInstance from '../api/axios'

export interface JoinRequestI {
  uuid: string
  // TODO: other fields
}

export const useJoinRequestsStore = defineStore('join_requests', {
  state: () => ({
    joinRequests: [] as JoinRequestI[],
  }),
  actions: {
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
    }
  },
  persist: true
})
