import { defineStore } from 'pinia'
import axiosInstance from '../api/axios'

export const invitationTypes = ['user', 'group'] as const
export type InvitationType = typeof invitationTypes[number]

export const invitationLifeTimeTypes = ['10m', '1h', '1d', 'unlimited'] as const
export type InvitationLifeTimeType = typeof invitationLifeTimeTypes[number]

export interface InvitationI {
  uuid: string
  invitation_type: InvitationType
  lifetime: InvitationLifeTimeType
  max_uses: number | null

  group_uuid: string | null
}

export const useInvitationStore = defineStore('invitations', {
  state: () => ({
    userInvitations: [] as InvitationI[],
    groupInvitations: [] as InvitationI[],
  }),
  actions: {
    getInvitationsByGroupUuid(uuid: string) {
      return this.groupInvitations.filter(i => i.group_uuid === uuid)
    },
    async fetchUserInvitations() {
      try {
        const response = await axiosInstance.get("/invitations/user")
        const data = response.data // total, items->invitations
        this.userInvitations = data.items as InvitationI[]
      } catch (error) {
        console.error("Error fetching user invitations:", error)
      }
    },
    async fetchGroupInvitations(groupUuid: string) {
      try {
        const response = await axiosInstance.get(`/invitations/group?group_uuid=${groupUuid}`)
        const data = response.data // total, items->invitations
        this.groupInvitations = data.items as InvitationI[]
      } catch (error) {
        console.error("Error fetching group invitations:", error)
      }
    },
    async createInvitation(
        invitationType: InvitationType,
        lifetime: InvitationLifeTimeType,
        maxUses: number | null,
        groupUuid: string | null
    ) {
      try {
        const payload = {
            invitation_type: invitationType,
            lifetime: lifetime,
            max_uses: maxUses,
            group_uuid: groupUuid
        };
        const response = await axiosInstance.post('/invitations/', payload, {
          headers: { 'Accept': 'application/json' },
        });

        const invitation = response.data as InvitationI
        if (invitationType === 'user')
          this.userInvitations.push(invitation)
        else if (invitationType === 'group')
          this.groupInvitations.push(invitation)

      } catch (error) {
        console.error("Error creating invitation: ", error)
      }
    },
    async deleteInvitation(invitationUuid: string) {
      try {
        const response = await axiosInstance.delete(`/invitations?invitation_uuid=${invitationUuid}`)
        if (!response.data.success) {
          console.error("Invitation was not deleted")
          return
        }

        this.groupInvitations = this.groupInvitations.filter(i => i.uuid !== invitationUuid)
        this.userInvitations = this.userInvitations.filter(i => i.uuid !== invitationUuid)
      } catch (error) {
        console.error("Error deleting invitation:", error)
      }
    },
    async join_via_invitation(invitationUuid: string) {
      try {
        const response = await axiosInstance.get(`/invitations/join?invitation_uuid=${invitationUuid}`)
        if (!response.data.success) {
          console.error("Invitation join failed")
          return
        }
      } catch (error) {
        console.error("Error deleting invitation:", error)
      }
    }
  },
  persist: true
})