import { defineStore } from 'pinia'
import { authApi } from '@/api'
import type { User, LoginRequest, AuthTokens } from '@/types'

export const useUserStore = defineStore('user', {
  state: () => ({
    accessToken: localStorage.getItem('access_token') || '',
    refreshToken: localStorage.getItem('refresh_token') || '',
    user: localStorage.getItem('user')
      ? JSON.parse(localStorage.getItem('user') ?? 'null') as User | null
      : null as User | null,
    isInitialized: false
  }),

  getters: {
    isLoggedIn: (state): boolean => !!state.accessToken && !!state.user
  },

  actions: {
    async login(credentials: LoginRequest) {
      const tokens = await authApi.login(credentials) as unknown as AuthTokens
      this.accessToken = tokens.access
      this.refreshToken = tokens.refresh
      localStorage.setItem('access_token', tokens.access)
      localStorage.setItem('refresh_token', tokens.refresh)

      // Fetch user profile after login
      await this.fetchUser()
    },

    async logout() {
      try {
        if (this.refreshToken) {
          await authApi.logout({ refresh: this.refreshToken })
        }
      } catch {
        // Logout API may fail if token is already invalid — proceed anyway
      }

      this.accessToken = ''
      this.refreshToken = ''
      this.user = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
    },

    async fetchUser() {
      const user = await authApi.me() as unknown as User
      this.user = user
      localStorage.setItem('user', JSON.stringify(user))
    },

    async initialize() {
      if (!this.accessToken) {
        this.isInitialized = true
        return
      }
      try {
        await this.fetchUser()
      } catch {
        this.accessToken = ''
        this.refreshToken = ''
        this.user = null
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
      }
      this.isInitialized = true
    }
  }
})
