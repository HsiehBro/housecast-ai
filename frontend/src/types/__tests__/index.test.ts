import { describe, it, expect } from 'vitest'
import type {
  User,
  LoginRequest,
  RegisterRequest,
  AuthTokens,
  House,
  HouseListResponse,
  HouseListParams,
  PredictionRequest,
  PredictionResponse,
  ExplanationItem,
  ExplanationResponse,
  ModelVersion,
  ApiError
} from '../index'

describe('TypeScript type definitions', () => {
  it('User interface accepts valid user data', () => {
    const user: User = {
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      phone: '13800138000',
      avatar: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    }
    expect(user.username).toBe('testuser')
    expect(user.avatar).toBeNull()
  })

  it('User interface allows avatar string', () => {
    const user: User = {
      id: 2,
      username: 'avataruser',
      email: 'a@b.com',
      phone: '',
      avatar: '/media/avatars/test.jpg',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    }
    expect(user.avatar).toBe('/media/avatars/test.jpg')
  })

  it('LoginRequest requires username and password', () => {
    const req: LoginRequest = { username: 'admin', password: '123456' }
    expect(req.username).toBe('admin')
    expect(req.password).toBe('123456')
  })

  it('RegisterRequest has optional phone', () => {
    const withPhone: RegisterRequest = {
      username: 'u', password: 'p', email: 'e@e.com', phone: '13800138000'
    }
    const withoutPhone: RegisterRequest = {
      username: 'u', password: 'p', email: 'e@e.com'
    }
    expect(withPhone.phone).toBe('13800138000')
    expect(withoutPhone.phone).toBeUndefined()
  })

  it('AuthTokens has access and refresh', () => {
    const tokens: AuthTokens = { access: 'acc', refresh: 'ref' }
    expect(tokens.access).toBe('acc')
    expect(tokens.refresh).toBe('ref')
  })

  it('House interface has all required fields', () => {
    const house: House = {
      id: 1, name: 'Test', address: 'Addr', district: '浦东新区',
      property_type: '住宅', area: 100, rooms: 3, halls: 2, bathrooms: 1,
      floor: 5, total_floors: 20, year: 2020, orientation: '南',
      decoration: '精装', price: '5000000.00', price_per_sqm: '50000.00',
      lat: 31.23, lng: 121.47, status: 'available',
      created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z'
    }
    expect(house.area).toBe(100)
    expect(house.price).toBe('5000000.00')
    expect(house.lat).toBe(31.23)
  })

  it('House allows null lat/lng', () => {
    const house: House = {
      id: 2, name: 'X', address: '', district: 'A',
      property_type: '住宅', area: 50, rooms: 1, halls: 1, bathrooms: 1,
      floor: 1, total_floors: 6, year: 2000, orientation: '南',
      decoration: '毛坯', price: '1000000.00', price_per_sqm: '20000.00',
      lat: null, lng: null, status: 'available',
      created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z'
    }
    expect(house.lat).toBeNull()
    expect(house.lng).toBeNull()
  })

  it('HouseListResponse has pagination fields', () => {
    const res: HouseListResponse = {
      count: 100, next: 'http://example.com?page=2', previous: null, results: []
    }
    expect(res.count).toBe(100)
    expect(res.next).toContain('page=2')
    expect(res.previous).toBeNull()
  })

  it('HouseListParams has optional fields', () => {
    const empty: HouseListParams = {}
    const full: HouseListParams = { page: 2, page_size: 50, district: '浦东新区', ordering: '-price' }
    expect(empty.page).toBeUndefined()
    expect(full.page_size).toBe(50)
  })

  it('PredictionRequest has required and optional fields', () => {
    const minimal: PredictionRequest = { area: 100, rooms: 3, year: 2020, district: '浦东新区' }
    const full: PredictionRequest = { area: 100, rooms: 3, year: 2020, district: '浦东新区', floor: 5, lat: 31.23, lng: 121.47 }
    expect(minimal.floor).toBeUndefined()
    expect(full.floor).toBe(5)
  })

  it('PredictionResponse has correct shape', () => {
    const res: PredictionResponse = {
      predicted_price: 5000000, confidence: 0.85,
      feature_importance: { area: 0.35, rooms: 0.25 },
      input_data: { area: 100 }
    }
    expect(res.predicted_price).toBe(5000000)
    expect(res.feature_importance.area).toBe(0.35)
  })

  it('ExplanationItem impact is positive or negative', () => {
    const pos: ExplanationItem = { feature: 'area', importance: 0.5, shap_value: 0.3, impact: 'positive' }
    const neg: ExplanationItem = { feature: 'rooms', importance: 0.2, shap_value: -0.1, impact: 'negative' }
    expect(pos.impact).toBe('positive')
    expect(neg.impact).toBe('negative')
  })

  it('ExplanationResponse has correct shape', () => {
    const res: ExplanationResponse = {
      shap_values: [[0.1, -0.2]],
      explanations: [{ feature: 'area', importance: 0.5, shap_value: 0.1, impact: 'positive' }],
      base_value: 500000
    }
    expect(res.base_value).toBe(500000)
    expect(res.explanations).toHaveLength(1)
  })

  it('ModelVersion has correct shape', () => {
    const v: ModelVersion = {
      version: 1, model_type: 'xgboost', timestamp: '2024-01-01T00:00:00Z',
      metadata: { rmse: 1000 }, model_hash: 'abc123'
    }
    expect(v.version).toBe(1)
  })

  it('ApiError accepts various error formats', () => {
    const detail: ApiError = { detail: 'Not found' }
    const error: ApiError = { error: 'Something failed' }
    const field: ApiError = { username: ['This field is required.'] }
    expect(detail.detail).toBe('Not found')
    expect(error.error).toBe('Something failed')
    expect(field.username).toBeDefined()
  })
})
