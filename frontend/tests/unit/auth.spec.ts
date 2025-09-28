import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../../src/store/auth'

// mock axiosInstance
vi.mock('../../src/api/axios', () => ({
  default: {
    post: vi.fn(),
  },
}))

import axiosInstance from '../../src/api/axios'

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('sets user and token after login', async () => {
    const auth = useAuthStore();
    
    (axiosInstance.post as any).mockResolvedValueOnce({
      data: {
        access_token: 'fake-token',
        user: { username: 'testuser', email: 'test@example.com' },
      }
    })

    await auth.login('test@example.com', 'password123')

    expect(auth.isLoggedIn).toBe(true)
    expect(auth.accessToken).toBe('fake-token')
    expect(auth.currentUser?.username).toBe('testuser')
  })

  it('clears state after logout', async () => {
    const auth = useAuthStore()
    auth.accessToken = 'something'
    auth.isLoggedIn = true
    auth.currentUser = { username: 'me' } as any;

    (axiosInstance.post as any).mockResolvedValueOnce({})

    await auth.logout()

    expect(auth.isLoggedIn).toBe(false)
    expect(auth.accessToken).toBeNull()
    expect(auth.currentUser).toBeNull()
  })
})
