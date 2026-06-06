import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import ChartsView from '../ChartsView.vue'

vi.mock('@/api', () => ({
  housesApi: {
    list: vi.fn().mockResolvedValue({
      count: 0, next: null, previous: null, results: []
    })
  }
}))

vi.mock('echarts', () => ({
  default: {
    init: vi.fn().mockReturnValue({
      setOption: vi.fn(),
      resize: vi.fn(),
      dispose: vi.fn()
    })
  }
}))

describe('ChartsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('renders charts view', () => {
    const wrapper = mount(ChartsView, {
      global: { plugins: [ElementPlus] }
    })
    expect(wrapper.find('.charts-view').exists()).toBe(true)
  })

  it('renders three chart cards', () => {
    const wrapper = mount(ChartsView, {
      global: { plugins: [ElementPlus] }
    })
    const cards = wrapper.findAll('.chart-card')
    expect(cards.length).toBe(3)
  })

  it('renders chart containers', () => {
    const wrapper = mount(ChartsView, {
      global: { plugins: [ElementPlus] }
    })
    const containers = wrapper.findAll('.chart-container')
    expect(containers.length).toBe(3)
  })
})
