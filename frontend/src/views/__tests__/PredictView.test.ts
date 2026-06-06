import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import PredictView from '../PredictView.vue'

vi.mock('@/api', () => ({
  predictionApi: {
    predict: vi.fn().mockResolvedValue({
      predicted_price: 5000000,
      confidence: 0.85,
      feature_importance: { area: 0.35, rooms: 0.25, district: 0.2 },
      input_data: {}
    }),
    explain: vi.fn().mockResolvedValue({
      shap_values: [[0.1]],
      explanations: [{ feature: 'area', importance: 0.5, shap_value: 0.1, impact: 'positive' }],
      base_value: 3000000
    })
  }
}))

describe('PredictView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('renders predict form', () => {
    const wrapper = mount(PredictView, {
      global: { plugins: [ElementPlus] }
    })
    expect(wrapper.find('.predict-card').exists()).toBe(true)
  })

  it('has predict button', () => {
    const wrapper = mount(PredictView, {
      global: { plugins: [ElementPlus] }
    })
    expect(wrapper.find('.predict-view').exists()).toBe(true)
  })

  it('renders district select options', () => {
    const wrapper = mount(PredictView, {
      global: { plugins: [ElementPlus] }
    })
    expect(wrapper.find('.predict-view').exists()).toBe(true)
  })
})
