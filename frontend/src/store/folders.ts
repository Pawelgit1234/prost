import { defineStore } from 'pinia'

export interface FolderType {
  uuid: string
  name: string
  pos: number
}

export const useFolderStore = defineStore('folders', {
  state: () => ({
    folders: [] as FolderType[],
    selectedFolderUuid: '' as string
  }),
  actions: {
    addFolder(folder: FolderType) {
      this.folders.push(folder)
    },
    selectFolder(uuid: string) {
      this.selectedFolderUuid = uuid
    }
  },
  persist: true
})
