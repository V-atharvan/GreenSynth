/**
 * GreenSynth Analytics — Centralized API Client
 *
 * All HTTP requests go through this axios instance.
 * Attaches JWT Bearer authentication headers and normalizes API error responses.
 */

import axios from 'axios'
import type { ApiError } from '@/types'

// ── Storage Keys & Events ──────────────────────────────────
export const AUTH_TOKEN_KEY = 'greensynth_token'
export const AUTH_UNAUTHORIZED_EVENT = 'greensynth:unauthorized'

// ── Base URL ──────────────────────────────────────────────
// In development: Vite proxy forwards /api → backend:8000
// In Docker: VITE_API_BASE_URL set to http://backend:8000
const BASE_URL = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/api/v1`
  : '/api/v1'

// ── Axios instance ─────────────────────────────────────────
export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60s timeout to allow Render free tier cold-start wakeups (30-50s)
})

// ── Request interceptor ────────────────────────────────────
// Attaches Bearer JWT token if available in localStorage.
apiClient.interceptors.request.use((config) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem(AUTH_TOKEN_KEY) : null
  if (token && token.trim().length > 0 && config.headers) {
    if (!config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

// ── Response interceptor ───────────────────────────────────
// Normalizes API errors to a consistent shape and handles session expiry.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response

      // Extract formatted message
      let message = 'An unexpected error occurred.'
      if (typeof data?.detail === 'string') {
        message = data.detail
      } else if (typeof data?.detail?.message === 'string') {
        message = data.detail.message
      } else if (typeof data?.message === 'string') {
        message = data.message
      } else if (Array.isArray(data?.detail) && data.detail.length > 0) {
        // FastAPI / Pydantic validation error list
        message = data.detail.map((err: any) => err.msg || `${err.loc?.join('.')} is invalid`).join(', ')
      }

      // Handle 401 Unauthorized: Expired/invalid session
      if (status === 401) {
        if (typeof window !== 'undefined') {
          localStorage.removeItem(AUTH_TOKEN_KEY)
          window.dispatchEvent(new CustomEvent(AUTH_UNAUTHORIZED_EVENT))
        }
      }

      const apiError: ApiError = {
        error_code: data?.error_code ?? (typeof data?.detail?.code === 'string' ? data.detail.code : `HTTP_${status}`),
        message,
        field: data?.field,
        suggestion: data?.suggestion,
      }
      return Promise.reject(apiError)
    }

    if (error.request) {
      return Promise.reject({
        error_code: 'NETWORK_ERROR',
        message: 'Cannot reach the GreenSynth server. Please check your connection.',
      } satisfies ApiError)
    }

    return Promise.reject({
      error_code: 'CLIENT_ERROR',
      message: error.message ?? 'An unexpected client error occurred.',
    } satisfies ApiError)
  }
)

export default apiClient
