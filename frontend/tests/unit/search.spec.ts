import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSearchStore } from '../../src/store/search'

// mock axiosInstance
vi.mock('../../src/api/axios', () => {
  return {
    default: {
      get: vi.fn(),
    },
  }
})

import axiosInstance from '../../src/api/axios'

describe('Search Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('resets search state', () => {
    const store = useSearchStore()
    store.query = 'hello'
    store.items = [{ uuid: '1', type: 'users' }]
    store.page = 3
    store.total = 100
    store.hasMore = false

    store.reset('new query')

    expect(store.query).toBe('new query')
    expect(store.items).toEqual([])
    expect(store.page).toBe(1)
    expect(store.total).toBe(0)
    expect(store.hasMore).toBe(true)
  })

  it('fetchSearchPage appends items and updates total/page correctly', async () => {
    const store = useSearchStore()
    store.query = 'test'
    store.page = 1
    store.hasMore = true

    ;(axiosInstance.get as any).mockResolvedValueOnce({
      data: {
        total: 3,
        items: [
          { uuid: '1', type: 'users', username: 'user1' },
          { uuid: '2', type: 'chats', name: 'chat1', is_yours: false },
        ]
      }
    })

    await store.fetchSearchPage()

    expect(store.items).toHaveLength(2)
    expect(store.total).toBe(3)
    expect(store.page).toBe(2)
    expect(store.hasMore).toBe(true)

    // second page
    ;(axiosInstance.get as any).mockResolvedValueOnce({
      data: {
        total: 3,
        items: [
          { uuid: '3', type: 'messages', text: 'hello' },
        ]
      }
    })

    await store.fetchSearchPage()
    expect(store.items).toHaveLength(3)
    expect(store.hasMore).toBe(false)
  })

  it('loads history from API', async () => {
    const store = useSearchStore()

    ;(axiosInstance.get as any).mockResolvedValueOnce({
      data: {
        items: ['first query', 'second query']
      }
    })

    await store.loadHistory()

    expect(store.queries).toEqual(['first query', 'second query'])
  })
})
