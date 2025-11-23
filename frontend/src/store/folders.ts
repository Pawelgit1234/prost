import { defineStore } from 'pinia'
import axiosInstance from '../api/axios'

export const protectedTypes = ['all', 'chats', 'groups', 'new']

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
          this.folders.forEach((folder, index) => {folder.position = index})
        } else {
          console.error("Folder was not deleted")
        }
      } catch (error) {
        console.error("Error deleting folder: ", error)
      }
    },
    async renameFolder(uuid: string, newName: string) {
      try {
        const payload = { name: newName };
        const response = await axiosInstance.patch(`/folders/${uuid}/rename`, payload, {
          headers: { 'Accept': 'application/json' },
        });

        if (response.data.success) {
          const folder = this.folders.find(f => f.uuid === uuid)
          if (folder) {
            folder.name = newName;
          }
        } else {
          console.error("Folder was not renamed")
        }
      } catch (error) {
        console.error("Error renaming folder: ", error)
      }
    },
    async replaceChats(folderUuid: string, chatUuids: string[]) {
      try {
        const payload = { uuids: chatUuids };
        const response = await axiosInstance.put(`/folders/${folderUuid}/chats`, payload, {
          headers: { 'Accept': 'application/json' },
        });

        if (response.data.success) {
          const folder = this.folders.find(f => f.uuid === folderUuid)
          if (folder) {
            folder.chat_uuids = chatUuids
            folder.pinned_chats = folder.pinned_chats.filter(uuid => chatUuids.includes(uuid)) 
          }
        } else {
          console.error("Chats in the folder were not replaced")
        }
      } catch (error) {
        console.error("Error replacing chats in the folder: ", error)
      }
    },
    async updateOrder() {
      try {
        const payload = { folders: this.folders.map(f => ({
          uuid: f.uuid,
          position: f.position
        }))}
        const response = await axiosInstance.put(`/folders/order`, payload, {
          headers: { 'Accept': 'application/json' },
        });

        if (!response.data.success)
          console.error("Folder order were not updated")
      } catch (error) {
        console.error("Error updating folder order: ", error)
      }
    }
  },
  persist: true
})

