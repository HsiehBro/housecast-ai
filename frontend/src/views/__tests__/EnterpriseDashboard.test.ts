import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import EnterpriseDashboard from '../EnterpriseDashboard.vue'

vi.mock('@/api', () => ({
  housesApi: {
    list: vi.fn().mockResolvedValue({
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id: 1, name: 'Test1', address: 'Addr1', district: '浦东新区',
          property_type: '住宅', area: 100, rooms: 3, halls: 2, bathrooms: 1,
          floor: 5, total_floors: 20, year: 2020, orientation: '南',
          decoration: '精装', price: '5000000.00', price_per_sqm: '50000.00',
          lat: 31.23, lng: 121.47, status: 'available',
          created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z'
        },
        {
          id: 2, name: 'Test2', address: 'Addr2', district: '黄浦区',
          property_type: '公寓', area: 80, rooms: 2, halls: 1, bathrooms: 1,
          floor: 10, total_floors: 30, year: 2018, orientation: '东',
          decoration: '简装', price: '8000000.00', price_per_sqm: '100000.00',
          lat: 31.22, lng: 121.48, status: 'available',
          created_at: '2024-01-02T00:00:00Z', updated_at: '2024-01-02T00:00:00Z'
        }
      ]
    })
  }
}))

// Mock echarts since jsdom doesn't have canvas
vi.mock('echarts', () => ({
  default: {
    init: vi.fn().mockReturnValue({
      setOption: vi.fn(),
      resize: vi.fn(),
      dispose: vi.fn()
    })
  }
}))

describe('EnterpriseDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('renders dashboard container', () => {
    const wrapper = mount(EnterpriseDashboard, {
      global: { plugins: [ElementPlus] }
    })
    expect(wrapper.find('.dashboard').exists()).toBe(true)
  })

  it('renders four stat cards', () => {
    const wrapper = mount(EnterpriseDashboard, {
      global: { plugins: [ElementPlus] }
    })
    const cards = wrapper.findAll('.stat-card')
    expect(cards.length).toBe(4)
  })

  it('renders chart containers', () => {
    const wrapper = mount(EnterpriseDashboard, {
      global: { plugins: [ElementPlus] }
    })
    expect(wrapper.find('.charts-section').exists()).toBe(true)
  })

  it('shows loading state initially', () => {
    const wrapper = mount(EnterpriseDashboard, {
      global: { plugins: [ElementPlus] }
    })
    // The component starts with loading=true
    expect(wrapper.vm.loading).toBe(true)
  })
})
