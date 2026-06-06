import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import RegisterView from '../RegisterView.vue'

vi.mock('@/api', () => ({
  authApi: {
    register: vi.fn().mockResolvedValue({ id: 1, username: 'newuser' }),
    login: vi.fn().mockResolvedValue({ access: 'token', refresh: 'refresh' }),
    me: vi.fn().mockResolvedValue({
      id: 1, username: 'newuser', email: 'new@test.com',
      phone: '', avatar: null, created_at: '', updated_at: ''
    })
  }
}))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/', name: 'Dashboard', component: { template: '<div>' } },
    { path: '/login', name: 'Login', component: { template: '<div>' } },
    { path: '/register', name: 'Register', component: RegisterView }
  ]
})

describe('RegisterView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('renders register form', () => {
    const wrapper = mount(RegisterView, {
      global: { plugins: [router, ElementPlus] }
    })
    expect(wrapper.find('.register-card').exists()).toBe(true)
  })

  it('has register button', () => {
    const wrapper = mount(RegisterView, {
      global: { plugins: [router, ElementPlus] }
    })
    expect(wrapper.find('.register-button').exists()).toBe(true)
  })

  it('has link to login page', () => {
    const wrapper = mount(RegisterView, {
      global: { plugins: [router, ElementPlus] }
    })
    const link = wrapper.find('.login-link a')
    expect(link.exists()).toBe(true)
    const href = link.attributes('href') || link.attributes('to')
    expect(href).toContain('/login')
  })
})
