import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import ProfileView from '../ProfileView.vue'

vi.mock('@/api', () => ({
  authApi: {
    me: vi.fn().mockResolvedValue({
      id: 1, username: 'testuser', email: 'test@test.com',
      phone: '13800138000', avatar: null,
      created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z'
    }),
    updateMe: vi.fn().mockResolvedValue({
      id: 1, username: 'updated', email: 'new@test.com',
      phone: '13900139000', avatar: null,
      created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-02T00:00:00Z'
    })
  }
}))

describe('ProfileView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('renders profile view', () => {
    const wrapper = mount(ProfileView, {
      global: { plugins: [ElementPlus] }
    })
    expect(wrapper.find('.profile-view').exists()).toBe(true)
  })

  it('renders user card', () => {
    const wrapper = mount(ProfileView, {
      global: { plugins: [ElementPlus] }
    })
    expect(wrapper.find('.user-card').exists()).toBe(true)
  })

  it('renders menu items', () => {
    const wrapper = mount(ProfileView, {
      global: { plugins: [ElementPlus] }
    })
    const menuItems = wrapper.findAll('.el-menu-item')
    expect(menuItems.length).toBe(2) // basic + password
  })
})
