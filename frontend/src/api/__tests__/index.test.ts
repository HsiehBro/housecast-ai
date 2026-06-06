import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'

// We test the API module by importing it after mocking axios
vi.mock('axios', () => {
  const mockAxiosInstance = {
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() }
    },
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
  return {
    default: {
      create: () => mockAxiosInstance
    }
  }
})

// Mock element-plus ElMessage
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warning: vi.fn()
  }
}))

describe('API module', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('creates axios instance with correct baseURL', async () => {
    const mod = await import('../index')
    expect(mod.default).toBeDefined()
  })

  it('authApi.login calls POST /auth/login/', async () => {
    const mod = await import('../index')
    const mockPost = mod.default.post as ReturnType<typeof vi.fn>
    mockPost.mockResolvedValueOnce({ data: { access: 'a', refresh: 'r' } })

    await mod.authApi.login({ username: 'admin', password: '123456' })
    expect(mockPost).toHaveBeenCalledWith('/auth/login/', { username: 'admin', password: '123456' })
  })

  it('authApi.register calls POST /auth/register/', async () => {
    const mod = await import('../index')
    const mockPost = mod.default.post as ReturnType<typeof vi.fn>
    mockPost.mockResolvedValueOnce({ data: { id: 1, username: 'newuser' } })

    await mod.authApi.register({
      username: 'newuser', password: '123456',
      password_confirm: '123456', email: 'new@test.com'
    })
    expect(mockPost).toHaveBeenCalledWith('/auth/register/', {
      username: 'newuser', password: '123456',
      password_confirm: '123456', email: 'new@test.com'
    })
  })

  it('authApi.logout calls POST /auth/logout/', async () => {
    const mod = await import('../index')
    const mockPost = mod.default.post as ReturnType<typeof vi.fn>
    mockPost.mockResolvedValueOnce({ data: { detail: 'ok' } })

    await mod.authApi.logout({ refresh: 'token' })
    expect(mockPost).toHaveBeenCalledWith('/auth/logout/', { refresh: 'token' })
  })

  it('authApi.refresh calls POST /auth/refresh/', async () => {
    const mod = await import('../index')
    const mockPost = mod.default.post as ReturnType<typeof vi.fn>
    mockPost.mockResolvedValueOnce({ data: { access: 'new', refresh: 'newr' } })

    await mod.authApi.refresh({ refresh: 'old' })
    expect(mockPost).toHaveBeenCalledWith('/auth/refresh/', { refresh: 'old' })
  })

  it('authApi.me calls GET /auth/me/', async () => {
    const mod = await import('../index')
    const mockGet = mod.default.get as ReturnType<typeof vi.fn>
    mockGet.mockResolvedValueOnce({ data: { id: 1, username: 'admin' } })

    await mod.authApi.me()
    expect(mockGet).toHaveBeenCalledWith('/auth/me/')
  })

  it('housesApi.list calls GET /houses/ with params', async () => {
    const mod = await import('../index')
    const mockGet = mod.default.get as ReturnType<typeof vi.fn>
    mockGet.mockResolvedValueOnce({ data: { count: 0, results: [] } })

    await mod.housesApi.list({ page: 1, page_size: 20 })
    expect(mockGet).toHaveBeenCalledWith('/houses/', { params: { page: 1, page_size: 20 } })
  })

  it('housesApi.create calls POST /houses/', async () => {
    const mod = await import('../index')
    const mockPost = mod.default.post as ReturnType<typeof vi.fn>
    const data = { name: 'Test', district: 'Pudong', area: 100, rooms: 3, floor: 5, year: 2020, price: '5000000' }
    mockPost.mockResolvedValueOnce({ data: { id: 1, ...data } })

    await mod.housesApi.create(data)
    expect(mockPost).toHaveBeenCalledWith('/houses/', data)
  })

  it('housesApi.detail calls GET /houses/{id}/', async () => {
    const mod = await import('../index')
    const mockGet = mod.default.get as ReturnType<typeof vi.fn>
    mockGet.mockResolvedValueOnce({ data: { id: 1 } })

    await mod.housesApi.detail(1)
    expect(mockGet).toHaveBeenCalledWith('/houses/1/')
  })

  it('housesApi.update calls PUT /houses/{id}/', async () => {
    const mod = await import('../index')
    const mockPut = mod.default.put as ReturnType<typeof vi.fn>
    const data = { name: 'Updated' }
    mockPut.mockResolvedValueOnce({ data: { id: 1, name: 'Updated' } })

    await mod.housesApi.update(1, data)
    expect(mockPut).toHaveBeenCalledWith('/houses/1/', data)
  })

  it('housesApi.delete calls DELETE /houses/{id}/', async () => {
    const mod = await import('../index')
    const mockDelete = mod.default.delete as ReturnType<typeof vi.fn>
    mockDelete.mockResolvedValueOnce({ status: 204 })

    await mod.housesApi.delete(1)
    expect(mockDelete).toHaveBeenCalledWith('/houses/1/')
  })

  it('predictionApi.predict calls POST /prediction/predict/', async () => {
    const mod = await import('../index')
    const mockPost = mod.default.post as ReturnType<typeof vi.fn>
    mockPost.mockResolvedValueOnce({ data: { predicted_price: 5000000, confidence: 0.85, feature_importance: {} } })

    await mod.predictionApi.predict({ area: 100, rooms: 3, year: 2020, district: '浦东新区' })
    expect(mockPost).toHaveBeenCalledWith('/prediction/predict/', { area: 100, rooms: 3, year: 2020, district: '浦东新区' })
  })

  it('predictionApi.explain calls POST /prediction/explain/', async () => {
    const mod = await import('../index')
    const mockPost = mod.default.post as ReturnType<typeof vi.fn>
    mockPost.mockResolvedValueOnce({ data: { explanations: [], base_value: 0 } })

    await mod.predictionApi.explain({ area: 100, rooms: 3, year: 2020, district: '浦东新区' })
    expect(mockPost).toHaveBeenCalledWith('/prediction/explain/', { area: 100, rooms: 3, year: 2020, district: '浦东新区' })
  })

  it('predictionApi.modelInfo calls GET /prediction/model-info/', async () => {
    const mod = await import('../index')
    const mockGet = mod.default.get as ReturnType<typeof vi.fn>
    mockGet.mockResolvedValueOnce({ data: {} })

    await mod.predictionApi.modelInfo()
    expect(mockGet).toHaveBeenCalledWith('/prediction/model-info/')
  })

  it('predictionApi.versions calls GET /prediction/versions/', async () => {
    const mod = await import('../index')
    const mockGet = mod.default.get as ReturnType<typeof vi.fn>
    mockGet.mockResolvedValueOnce({ data: { versions: [] } })

    await mod.predictionApi.versions()
    expect(mockGet).toHaveBeenCalledWith('/prediction/versions/')
  })

  it('predictionApi.currentVersion calls GET /prediction/versions/current/', async () => {
    const mod = await import('../index')
    const mockGet = mod.default.get as ReturnType<typeof vi.fn>
    mockGet.mockResolvedValueOnce({ data: {} })

    await mod.predictionApi.currentVersion()
    expect(mockGet).toHaveBeenCalledWith('/prediction/versions/current/')
  })

  it('predictionApi.rollback calls POST /prediction/versions/rollback/', async () => {
    const mod = await import('../index')
    const mockPost = mod.default.post as ReturnType<typeof vi.fn>
    mockPost.mockResolvedValueOnce({ data: {} })

    await mod.predictionApi.rollback({ version: 1 })
    expect(mockPost).toHaveBeenCalledWith('/prediction/versions/rollback/', { version: 1 })
  })
})
