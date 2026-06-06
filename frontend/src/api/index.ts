import axios from 'axios'
import { ElMessage } from 'element-plus'
import type {
  User,
  LoginRequest,
  RegisterRequest,
  AuthTokens,
  ChangePasswordRequest,
  House,
  HouseListResponse,
  HouseListParams,
  MapHouse,
  MapHouseParams,
  PredictionRequest,
  PredictionResponse,
  ExplanationResponse,
  ModelVersion,
  TrendData,
  ApiError
} from '@/types'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 10000
})

// Request interceptor: attach Bearer token
request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// Response interceptor: extract data, handle errors
request.interceptors.response.use(
  response => response.data,
  async error => {
    const status = error.response?.status
    const data: ApiError = error.response?.data ?? {}

    // Extract human-readable message
    const message =
      data.detail || data.error || data.message
      || (typeof data === 'string' ? data : null)
      || (typeof data === 'object'
        ? Object.values(data).flatMap(v => Array.isArray(v) ? v : [v])[0] as string
        : null)
      || error.message
      || '请求失败'

    // On 401, try refresh token once
    if (status === 401) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken && !error.config._retry) {
        error.config._retry = true
        try {
          const res = await axios.post(
            `${request.defaults.baseURL}/auth/refresh/`,
            { refresh: refreshToken }
          )
          const newAccess: string = res.data.access
          localStorage.setItem('access_token', newAccess)
          error.config.headers.Authorization = `Bearer ${newAccess}`
          return request(error.config)
        } catch {
          // Refresh failed — clear tokens and redirect
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user')
          window.location.href = '/login'
          return Promise.reject(error)
        }
      }
      // No refresh token available (e.g. wrong login credentials) — show error
      ElMessage.error(message)
    } else {
      // Show error notification for non-401 errors
      ElMessage.error(message)
    }

    return Promise.reject(error)
  }
)

// ===== Auth API =====

export const authApi = {
  login: (data: LoginRequest) =>
    request.post<AuthTokens>('/auth/login/', data),

  register: (data: RegisterRequest & { password_confirm: string }) =>
    request.post<User>('/auth/register/', data),

  logout: (data: { refresh: string }) =>
    request.post('/auth/logout/', data),

  refresh: (data: { refresh: string }) =>
    request.post<AuthTokens>('/auth/refresh/', data),

  me: () =>
    request.get<User>('/auth/me/'),

  updateMe: (data: Partial<User>) =>
    request.put<User>('/auth/me/', data),

  changePassword: (data: ChangePasswordRequest) =>
    request.post('/auth/change-password/', data)
}

// ===== Houses API =====

export const housesApi = {
  list: (params?: HouseListParams) =>
    request.get<HouseListResponse>('/houses/', { params }),

  mapList: (params?: MapHouseParams) =>
    request.get<MapHouse[]>('/houses/map/', { params, timeout: 20000 }),

  create: (data: Partial<House>) =>
    request.post<House>('/houses/', data),

  detail: (id: number) =>
    request.get<House>(`/houses/${id}/`),

  update: (id: number, data: Partial<House>) =>
    request.put<House>(`/houses/${id}/`, data),

  delete: (id: number) =>
    request.delete(`/houses/${id}/`)
}

// ===== Prediction API =====

export const predictionApi = {
  predict: (data: PredictionRequest) =>
    request.post<PredictionResponse>('/prediction/predict/', data),

  modelInfo: () =>
    request.get('/prediction/model-info/'),

  explain: (data: PredictionRequest) =>
    request.post<ExplanationResponse>('/prediction/explain/', data),

  versions: () =>
    request.get<{ versions: ModelVersion[] }>('/prediction/versions/'),

  currentVersion: () =>
    request.get<ModelVersion>('/prediction/versions/current/'),

  rollback: (data: { version: number }) =>
    request.post('/prediction/versions/rollback/', data),

  trend: (years: number) =>
    request.get<TrendData>('/prediction/trend/', { params: { years } })
}

export default request
