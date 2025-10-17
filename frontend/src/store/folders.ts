import { defineStore } from 'pinia'

import axiosInstance from '../api/axios'

export type FolderType = 'ALL' | 'CHATS' | 'GROUPS' | 'NEW' | 'CUSTOM';

export interface FolderI {
  uuid: string
  folder_type: FolderType
  name: string
  position: number

  pinnedChats: string[] // chat uuids
  chatUuids: string[] // chat uuids
}

export const useFolderStore = defineStore('folders', {
  state: () => ({
    folders: [] as FolderI[],
    selectedFolderUuid: '' as string
  }),
  actions: {
    addFolder(folder: FolderI) {
      this.folders.push(folder)
    },
    selectFolder(uuid: string) {
      this.selectedFolderUuid = uuid
    },
    async fetchFolders() {
      try {
        const response = await axiosInstance.get("/folders");
        const data = response.data; // total, items->folders
        this.folders = data.items as FolderI[];
      } catch (error) {
        console.log("Error during fetching all folders: ", error);
      }
    }
  },
  persist: true
})
