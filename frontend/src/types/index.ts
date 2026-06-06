// ===== User / Auth =====

export interface User {
  id: number
  username: string
  email: string
  phone: string
  avatar: string | null
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
  email: string
  phone?: string
}

export interface AuthTokens {
  access: string
  refresh: string
}

export interface ChangePasswordRequest {
  old_password: string
  new_password: string
  new_password_confirm: string
}

// ===== House =====

export interface House {
  id: number
  name: string
  address: string
  district: string
  property_type: string
  area: number
  rooms: number
  halls: number
  bathrooms: number
  floor: number
  total_floors: number
  year: number
  orientation: string
  decoration: string
  price: string
  price_per_sqm: string
  lat: number | null
  lng: number | null
  status: string
  created_at: string
  updated_at: string
}

export interface HouseListResponse {
  count: number
  next: string | null
  previous: string | null
  results: House[]
}

export interface HouseListParams {
  page?: number
  page_size?: number
  district?: string
  ordering?: string
  min_price?: number
  max_price?: number
  min_area?: number
  max_area?: number
  rooms?: number
}

export interface MapHouse {
  id: number
  name: string
  district: string
  area: number
  rooms: number
  floor: number
  year: number
  price: string
  price_per_sqm: string
  lat: number | null
  lng: number | null
}

export interface MapHouseParams {
  district?: string
  rooms?: number
  min_price?: number
  max_price?: number
  min_area?: number
  max_area?: number
}

// ===== Prediction =====

export interface PredictionRequest {
  area: number
  rooms: number
  year: number
  district: string
  floor?: number
  lat?: number
  lng?: number
}

export interface PredictionResponse {
  predicted_price: number
  confidence: number
  feature_importance: Record<string, number>
  input_data: Record<string, unknown>
}

export interface ExplanationItem {
  feature: string
  importance: number
  shap_value: number
  impact: 'positive' | 'negative'
}

export interface ExplanationResponse {
  shap_values: number[][]
  explanations: ExplanationItem[]
  base_value: number
}

export interface ModelVersion {
  version: number
  model_type: string
  timestamp: string
  metadata: Record<string, unknown>
  model_hash: string
}

// ===== Trend =====

export interface TrendPoint {
  year: number
  avg_price: number
}

export interface TrendData {
  historical: TrendPoint[]
  predicted: TrendPoint[]
  method: 'model' | 'cagr' | 'none'
}

// ===== API Error =====

export interface ApiError {
  detail?: string
  error?: string
  message?: string
  [key: string]: unknown
}
