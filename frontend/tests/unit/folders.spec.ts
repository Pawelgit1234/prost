import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useFolderStore, type FolderI } from '../../src/store/folders'

// mock axiosInstance
vi.mock('../../src/api/axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
    patch: vi.fn(),
    put: vi.fn(),
  },
}))

import axiosInstance from '../../src/api/axios'

describe('Folder Store', () => {
  let folderStore: ReturnType<typeof useFolderStore>

  const mockFolder: FolderI = {
    uuid: '1',
    folder_type: 'custom',
    name: 'Test Folder',
    position: 0,
    pinned_chats: [],
    chat_uuids: [],
  }

  beforeEach(() => {
    setActivePinia(createPinia())
    folderStore = useFolderStore()
    vi.clearAllMocks()
  })

  it('fetches folders and sets state', async () => {
    ;(axiosInstance.get as any).mockResolvedValueOnce({
      data: { items: [mockFolder] },
    })

    await folderStore.fetchFolders()

    expect(folderStore.folders).toHaveLength(1)
    expect(folderStore.folders[0].name).toBe('Test Folder')
  })

  it('creates a new folder', async () => {
    ;(axiosInstance.post as any).mockResolvedValueOnce({
      data: mockFolder,
    })

    await folderStore.createFolder('Test Folder')

    expect(folderStore.folders).toHaveLength(1)
    expect(folderStore.folders[0].name).toBe('Test Folder')
  })

  it('deletes a folder', async () => {
    folderStore.folders = [mockFolder]
    ;(axiosInstance.delete as any).mockResolvedValueOnce({
      data: { success: true },
    })

    await folderStore.deleteFolder(mockFolder.uuid)

    expect(folderStore.folders).toHaveLength(0)
  })

  it('renames a folder', async () => {
    folderStore.folders = [mockFolder]
    ;(axiosInstance.patch as any).mockResolvedValueOnce({
      data: { success: true },
    })

    await folderStore.renameFolder(mockFolder.uuid, 'New Name')

    expect(folderStore.folders[0].name).toBe('New Name')
  })

  it('replaces chats in a folder', async () => {
    folderStore.folders = [{ ...mockFolder, pinned_chats: ['1'] }]
    const newChats = ['2', '3']

    ;(axiosInstance.put as any).mockResolvedValueOnce({
      data: { success: true },
    })

    await folderStore.replaceChats(mockFolder.uuid, newChats)

    expect(folderStore.folders[0].chat_uuids).toEqual(newChats)
    expect(folderStore.folders[0].pinned_chats).toEqual([])
  })

  it('updates folder order', async () => {
    folderStore.folders = [mockFolder, { ...mockFolder, uuid: '2', position: 1 }]
    ;(axiosInstance.put as any).mockResolvedValueOnce({
      data: { success: true },
    })

    folderStore.folders[0].position = 1
    folderStore.folders[1].position = 0

    await folderStore.updateOrder()

    // test payload
    expect((axiosInstance.put as any).mock.calls[0][1]).toEqual({
      folders: [
        { uuid: '1', position: 1 },
        { uuid: '2', position: 0 },
      ],
    })
  })
})
