import { defineStore } from 'pinia'
import axiosInstance from '../api/axios'

export interface FolderI {
  uuid: string
  folder_type: string
  name: string
  position: number
  pinned_chats: string[] // chat uuids
  chat_uuids: string[]   // chat uuids
}

export const useFolderStore = defineStore('folders', {
  state: () => ({
    folders: [] as FolderI[],
    selectedFolderUuid: '' as string
  }),
  getters: {
    selectedFolder(state) {
      return state.folders.find(f => f.uuid === state.selectedFolderUuid)
    }
  },
  actions: {
    selectFolder(uuid: string) {
      this.selectedFolderUuid = uuid
    },
    addFolder(folder: FolderI) {
      this.folders.push(folder)
    },
    async fetchFolders() {
      try {
        const response = await axiosInstance.get("/folders")
        const data = response.data // total, items->folders
        this.folders = data.items as FolderI[]
      } catch (error) {
        console.error("Error fetching folders:", error)
      }
    }
  },
  persist: true
})

