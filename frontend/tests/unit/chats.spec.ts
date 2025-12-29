import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore, type ChatI } from '../../src/store/chats'
import { useFolderStore, type FolderI } from '../../src/store/folders'

// mock axios
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

describe('Chat Store', () => {
  let chatStore: ReturnType<typeof useChatStore>
  let folderStore: ReturnType<typeof useFolderStore>

  const mockChat: ChatI = {
    uuid: 'chat-1',
    chat_type: 'group',
    name: 'Test Chat',
    description: 'desc',
    avatar: undefined,
    is_open_for_messages: true,
    is_visible: true,
    last_message: undefined,
    created_at: '2024-01-01',
    updated_at: '2024-01-01',
    user_uuids: ['user-1'],
  }

  const mockFolder: FolderI = {
    uuid: 'folder-1',
    folder_type: 'custom',
    name: 'Folder',
    position: 0,
    pinned_chats: [],
    chat_uuids: ['chat-1'],
  }

  beforeEach(() => {
    setActivePinia(createPinia())
    chatStore = useChatStore()
    folderStore = useFolderStore()
    vi.clearAllMocks()
  })

  // ------------------------
  // basic actions
  // ------------------------

  it('selects a chat', () => {
    chatStore.chats = [mockChat]

    chatStore.selectChat(mockChat.uuid)

    expect(chatStore.selectedChatUuid).toBe(mockChat.uuid)
    expect(chatStore.selectedChat?.uuid).toBe(mockChat.uuid)
  })

  it('adds a chat', () => {
    chatStore.addChat(mockChat)

    expect(chatStore.chats).toHaveLength(1)
    expect(chatStore.chats[0].uuid).toBe(mockChat.uuid)
  })

  // ------------------------
  // fetch
  // ------------------------

  it('fetches chats and sets state', async () => {
    ;(axiosInstance.get as any).mockResolvedValueOnce({
      data: { items: [mockChat] },
    })

    await chatStore.fetchChats()

    expect(chatStore.chats).toHaveLength(1)
    expect(chatStore.chats[0].name).toBe('Test Chat')
  })

  // ------------------------
  // delete / quit
  // ------------------------

  it('quits chat', async () => {
    chatStore.chats = [mockChat]

    ;(axiosInstance.delete as any).mockResolvedValueOnce({
      data: { success: true },
    })

    await chatStore.quitChat(mockChat.uuid)

    expect(chatStore.chats).toHaveLength(0)
  })

  it('deletes chat', async () => {
    chatStore.chats = [mockChat]

    ;(axiosInstance.delete as any).mockResolvedValueOnce({
      data: { success: true },
    })

    await chatStore.deleteChat(mockChat.uuid)

    expect(chatStore.chats).toHaveLength(0)
  })

  // ------------------------
  // folders integration
  // ------------------------

  it('gets chats by folder', () => {
    chatStore.chats = [mockChat]
    folderStore.folders = [mockFolder]

    const chats = chatStore.getChatsByFolder(mockFolder)

    expect(chats).toHaveLength(1)
    expect(chats[0].uuid).toBe(mockChat.uuid)
  })

  it('getter chatsOfSelectedFolder works', () => {
    chatStore.chats = [mockChat]
    folderStore.folders = [mockFolder]
    folderStore.selectedFolderUuid = mockFolder.uuid

    const chats = chatStore.chatsOfSelectedFolder

    expect(chats).toHaveLength(1)
    expect(chats[0].uuid).toBe(mockChat.uuid)
  })

  // ------------------------
  // add users to group
  // ------------------------

  it('adds users to group', async () => {
    chatStore.chats = [mockChat]
    const newUsers = ['user-1', 'user-2']

    ;(axiosInstance.put as any).mockResolvedValueOnce({
      data: { success: true },
    })

    await chatStore.addUserToGroup(mockChat, newUsers)

    // payload check
    expect((axiosInstance.put as any).mock.calls[0][0]).toBe('/chats/add_user')
    expect((axiosInstance.put as any).mock.calls[0][1]).toEqual({
      group_uuid: mockChat.uuid,
      user_uuids: newUsers,
    })

    expect(mockChat.user_uuids).toEqual(newUsers)
  })
})
