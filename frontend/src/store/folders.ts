import { defineStore } from 'pinia'
import axiosInstance from '../api/axios'
import type { ChatI } from './chats'

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
    },
    async addChatToFolders(chat: ChatI, folders: FolderI[]) {
      try {
        const payload = { folder_uuids: folders.map(f => f.uuid) };
        const response = await axiosInstance.put(`/chats/${chat.uuid}/folders`, payload, {
          headers: { 'Accept': 'application/json' },
        });

        if (!response.data.success) {
          console.error("Folders were not updated")
          return
        }

        // delete from all folder
        for (const folder of this.folders) {
          const idx = folder.chat_uuids.indexOf(chat.uuid)
          if (idx !== -1) folder.chat_uuids.splice(idx, 1)
        }

        // add in folders user choosed
        for (const folder of folders) {
          if (!folder.chat_uuids.includes(chat.uuid)) {
            folder.chat_uuids.push(chat.uuid)
          }
        }
      } catch (error) {
        console.error("Error updating chat folders: ", error)
      }
    },
    async handlePin(folder_uuid: string, chat_uuid: string) {
      try {
        const response = await axiosInstance.put(`/chats/${chat_uuid}/folders/${folder_uuid}/pin`);
        const folder = this.folders.find(f => f.uuid === folder_uuid)
        if (!folder) return

        const index = folder.pinned_chats.indexOf(chat_uuid)
        if (index !== -1) {
          folder.pinned_chats.splice(index, 1)
        }
        if (response.data.is_pinned) {
          folder.pinned_chats.push(chat_uuid)
        }
      } catch (error) {
        console.error("Error pinning chat: ", error)
      }
    },
    isChatPinned(chat_uuid: string) {
      if (!this.selectedFolder) return
      const folder = this.selectedFolder

      const chat = folder.chat_uuids.find(c => c === chat_uuid)
      const pin = folder.pinned_chats.find(c => c === chat_uuid)
      return chat && pin
    }
  },
  persist: true
})

