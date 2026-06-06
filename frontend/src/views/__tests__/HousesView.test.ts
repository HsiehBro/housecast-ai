import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import HousesView from '../HousesView.vue'

vi.mock('@/api', () => ({
  housesApi: {
    list: vi.fn().mockResolvedValue({
      count: 0, next: null, previous: null, results: []
    }),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn()
  }
}))

describe('HousesView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('renders houses view', () => {
    const wrapper = mount(HousesView, {
      global: { plugins: [ElementPlus, createPinia()] }
    })
    expect(wrapper.find('.houses-view').exists()).toBe(true)
  })

  it('renders filter card', () => {
    const wrapper = mount(HousesView, {
      global: { plugins: [ElementPlus, createPinia()] }
    })
    expect(wrapper.find('.filter-card').exists()).toBe(true)
  })

  it('renders table card', () => {
    const wrapper = mount(HousesView, {
      global: { plugins: [ElementPlus, createPinia()] }
    })
    expect(wrapper.find('.table-card').exists()).toBe(true)
  })

  it('renders add button', () => {
    const wrapper = mount(HousesView, {
      global: { plugins: [ElementPlus, createPinia()] }
    })
    expect(wrapper.find('.table-header').exists()).toBe(true)
  })
})
