import { config } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'

config.global.plugins = [
  createTestingPinia({
    createSpy: vi.fn,
    stubActions: false
  })
]

// Mock Element Plus ElMessage
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      info: vi.fn(),
      warning: vi.fn()
    }
  }
})
