import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import MapView from '../MapView.vue'

vi.mock('@/api', () => ({
  housesApi: {
    list: vi.fn().mockResolvedValue({
      count: 0, next: null, previous: null, results: []
    })
  }
}))

describe('MapView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('renders map view', () => {
    const wrapper = mount(MapView, {
      global: { plugins: [ElementPlus] }
    })
    expect(wrapper.find('.map-view').exists()).toBe(true)
  })

  it('renders map container', () => {
    const wrapper = mount(MapView, {
      global: { plugins: [ElementPlus] }
    })
    expect(wrapper.find('#map-container').exists()).toBe(true)
  })

  it('has load and clear buttons', () => {
    const wrapper = mount(MapView, {
      global: { plugins: [ElementPlus] }
    })
    const buttons = wrapper.findAll('.controls .el-button')
    expect(buttons.length).toBe(2)
  })
})
