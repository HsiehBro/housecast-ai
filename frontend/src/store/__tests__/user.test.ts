import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useUserStore } from '../user'
import { authApi } from '@/api'
import type { User, AuthTokens } from '@/types'

vi.mock('@/api', () => ({
  authApi: {
    login: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
    me: vi.fn()
  }
}))

describe('useUserStore', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('initializes with no token/user from localStorage', () => {
    const store = useUserStore()
    expect(store.accessToken).toBe('')
    expect(store.user).toBeNull()
    expect(store.isLoggedIn).toBe(false)
  })

  it('initializes with token/user from localStorage', () => {
    localStorage.setItem('access_token', 'test-access')
    localStorage.setItem('refresh_token', 'test-refresh')
    localStorage.setItem('user', JSON.stringify({ id: 1, username: 'admin' }))
    setActivePinia(createPinia()) // Re-create pinia to pick up localStorage

    const store = useUserStore()
    expect(store.accessToken).toBe('test-access')
    expect(store.user).toEqual({ id: 1, username: 'admin' })
    expect(store.isLoggedIn).toBe(true)
  })

  it('login stores tokens and fetches user', async () => {
    const tokens: AuthTokens = { access: 'new-access', refresh: 'new-refresh' }
    const user: User = {
      id: 1, username: 'admin', email: 'a@b.com', phone: '',
      avatar: null, created_at: '', updated_at: ''
    }
    // Interceptor extracts response.data, so mock returns the data directly
    vi.mocked(authApi.login).mockResolvedValueOnce(tokens as never)
    vi.mocked(authApi.me).mockResolvedValueOnce(user as never)

    const store = useUserStore()
    await store.login({ username: 'admin', password: '123456' })

    expect(authApi.login).toHaveBeenCalledWith({ username: 'admin', password: '123456' })
    expect(store.accessToken).toBe('new-access')
    expect(store.refreshToken).toBe('new-refresh')
    expect(store.user).toEqual(user)
    expect(store.isLoggedIn).toBe(true)
    expect(localStorage.getItem('access_token')).toBe('new-access')
    expect(localStorage.getItem('refresh_token')).toBe('new-refresh')
  })

  it('logout clears state and localStorage', async () => {
    localStorage.setItem('access_token', 'old-access')
    localStorage.setItem('refresh_token', 'old-refresh')
    localStorage.setItem('user', JSON.stringify({ id: 1, username: 'admin' }))
    setActivePinia(createPinia())

    vi.mocked(authApi.logout).mockResolvedValueOnce({} as never)

    const store = useUserStore()
    await store.logout()

    expect(authApi.logout).toHaveBeenCalled()
    expect(store.accessToken).toBe('')
    expect(store.refreshToken).toBe('')
    expect(store.user).toBeNull()
    expect(store.isLoggedIn).toBe(false)
    expect(localStorage.getItem('access_token')).toBeNull()
  })

  it('isLoggedIn returns false when no token', () => {
    const store = useUserStore()
    expect(store.isLoggedIn).toBe(false)
  })

  it('fetchUser updates user from API', async () => {
    const user: User = {
      id: 1, username: 'admin', email: 'a@b.com', phone: '138',
      avatar: null, created_at: '', updated_at: ''
    }
    vi.mocked(authApi.me).mockResolvedValueOnce(user as never)
    localStorage.setItem('access_token', 'tok')
    localStorage.setItem('user', '{}')

    const store = useUserStore()
    await store.fetchUser()

    expect(authApi.me).toHaveBeenCalled()
    expect(store.user).toEqual(user)
    expect(JSON.parse(localStorage.getItem('user') || '{}')).toEqual(user)
  })
})
