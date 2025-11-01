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
    },
    async createFolder(name: string) {
      try {
        const response = await axiosInstance.post('/folders', { name })
        const folder = response.data as FolderI
        this.folders.push(folder)
      } catch (error) {
        console.error("Error creating new folder: ", error)
      }
    },
    async deleteFolder(uuid: string) {
      try {
        const response = await axiosInstance.delete('/folders/' + uuid + '/')
        if (response.data.success) {
          this.folders = this.folders.filter((folder) => folder.uuid !== uuid)
        } else {
          console.error("Folder was not deleted")
        }
      } catch (error) {
        console.error("Error deleting folder: ", error)
      }
    }
  },
  persist: true
})

