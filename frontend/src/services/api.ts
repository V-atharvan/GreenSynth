/**
 * GreenSynth Analytics — Centralized API Client
 *
 * All HTTP requests go through this axios instance.
 * Do NOT make API calls directly in React components.
 * Use the service layer (projectService, experimentService, etc.) instead.
 */

import axios from 'axios'
import type { ApiError } from '@/types'

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
  timeout: 15000,
})

// ── Response interceptor ───────────────────────────────────
// Normalizes API errors to a consistent shape.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const data = error.response.data
      const apiError: ApiError = {
        error_code: data?.error_code ?? 'API_ERROR',
        message: data?.detail ?? data?.message ?? 'An unexpected error occurred.',
        field: data?.field,
        suggestion: data?.suggestion,
      }
      return Promise.reject(apiError)
    }

    if (error.request) {
      return Promise.reject({
        error_code: 'NETWORK_ERROR',
        message: 'Cannot reach the server. Please check your connection.',
      } satisfies ApiError)
    }

    return Promise.reject({
      error_code: 'CLIENT_ERROR',
      message: error.message ?? 'An unexpected error occurred.',
    } satisfies ApiError)
  }
)

export default apiClient
